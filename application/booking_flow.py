"""Fluxo determinístico de agendamento por escolhas estruturadas.

O módulo não interpreta nomes nem horários enviados pelo cliente. A sessão
mantém as opções que vieram do Java e cada escolha é validada contra ela.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from threading import RLock
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

from infrastructure.java_vetsync_client import (
    JavaVetSyncClient,
    JavaVetSyncConflictError,
    JavaVetSyncError,
)


BOOKING_TIMEZONE = ZoneInfo("America/Sao_Paulo")
SESSION_TTL = timedelta(minutes=15)


class BookingFlowError(Exception):
    pass


@dataclass
class BookingOption:
    action: str
    data: dict[str, Any]
    label: str
    description: str | None = None


@dataclass
class BookingSession:
    id: str
    tutor_id: str
    expires_at: datetime
    state: str = "AGUARDANDO_DATA"
    selected: dict[str, Any] = field(default_factory=dict)
    options: dict[str, BookingOption] = field(default_factory=dict)


class BookingSessionStore:
    """Armazena sessões de curta duração no processo da SIA."""

    def __init__(self) -> None:
        self._sessions: dict[str, BookingSession] = {}
        self._lock = RLock()

    def create(self, tutor_id: str) -> BookingSession:
        with self._lock:
            self._cleanup()
            session = BookingSession(
                id=str(uuid4()),
                tutor_id=tutor_id,
                expires_at=datetime.now(BOOKING_TIMEZONE) + SESSION_TTL,
            )
            self._sessions[session.id] = session
            return session

    def get(self, session_id: str, tutor_id: str) -> BookingSession:
        with self._lock:
            self._cleanup()
            session = self._sessions.get(session_id)
            if not session or session.tutor_id != tutor_id:
                raise BookingFlowError("Essa etapa de agendamento expirou. Comece novamente para consultar os horários atuais.")
            session.expires_at = datetime.now(BOOKING_TIMEZONE) + SESSION_TTL
            return session

    def _cleanup(self) -> None:
        now = datetime.now(BOOKING_TIMEZONE)
        expired = [session_id for session_id, session in self._sessions.items() if session.expires_at <= now]
        for session_id in expired:
            del self._sessions[session_id]


@dataclass
class BookingFlowResponse:
    message: str
    block: dict[str, Any] | None = None

    def to_payload(self) -> dict[str, Any]:
        payload = {"mensagem": self.message}
        if self.block:
            payload["bloco"] = self.block
        return payload


class BookingFlowService:
    def __init__(self, java_client: JavaVetSyncClient, sessions: BookingSessionStore | None = None) -> None:
        self.java_client = java_client
        self.sessions = sessions or BookingSessionStore()

    def start(self, message: str, tutor_id: str, bearer_token: str) -> BookingFlowResponse:
        session = self.sessions.create(tutor_id)
        requested_date = self._resolve_date(message)
        if not requested_date:
            return self._show_date_options(session, "Para qual dia você quer a consulta?")

        session.selected["date"] = requested_date.isoformat()
        return self._show_general_slots(session, bearer_token, self._health_prefix(message))

    def select(self, session_id: str, option_id: str, tutor_id: str, bearer_token: str) -> BookingFlowResponse:
        session = self.sessions.get(session_id, tutor_id)
        option = session.options.get(option_id)
        if not option:
            raise BookingFlowError("Essa opção não é mais válida. Escolha uma das opções atuais.")

        if option.action == "DATE":
            session.selected["date"] = option.data["date"]
            return self._show_general_slots(session, bearer_token)
        if option.action == "SLOT":
            session.selected.update(option.data)
            return self._show_pet_options(session, bearer_token)
        if option.action == "PET":
            session.selected.update(option.data)
            return self._show_confirmation(session)
        if option.action == "CONFIRM":
            return self._confirm(session, bearer_token)
        if option.action == "CHANGE_SLOT":
            return self._show_general_slots(session, bearer_token, "Escolha outro horário para a consulta. ")
        raise BookingFlowError("Não reconheci essa escolha de agendamento.")

    def _show_date_options(self, session: BookingSession, message: str) -> BookingFlowResponse:
        today = datetime.now(BOOKING_TIMEZONE).date()
        choices = []
        for offset in range(0, 3):
            selected_date = today + timedelta(days=offset)
            choices.append(BookingOption(
                action="DATE",
                data={"date": selected_date.isoformat()},
                label=selected_date.strftime("%d/%m"),
                description=self._weekday_name(selected_date),
            ))
        return self._set_block(session, "AGUARDANDO_DATA", "SELECIONAR_DATA", "Escolha uma data", choices, message)

    def _show_general_slots(
        self,
        session: BookingSession,
        bearer_token: str,
        prefix: str = "",
    ) -> BookingFlowResponse:
        selected_date = session.selected.get("date")
        if not selected_date:
            return self._show_date_options(session, "Para qual dia você quer a consulta?")
        try:
            response = self.java_client.available_slots(bearer_token, selected_date, "CLINICO_GERAL")
        except JavaVetSyncError as exc:
            raise BookingFlowError("Não consegui consultar os horários da clínica agora. Tente novamente em instantes.") from exc

        slots = response.get("slots") if isinstance(response, dict) else None
        if not isinstance(slots, list):
            raise BookingFlowError("A agenda da clínica devolveu uma resposta inválida. Tente novamente em instantes.")
        choices = [
            BookingOption(
                action="SLOT",
                data={
                    "idTipoEvento": slot["idTipoEvento"],
                    "nmTipoEvento": slot["nmTipoEvento"],
                    "idVeterinario": slot["idVeterinario"],
                    "nmVeterinario": slot["nmVeterinario"],
                    "hrEvento": slot["hrEvento"],
                },
                label=slot["hrEvento"],
                description=slot["nmVeterinario"],
            )
            for slot in slots
            if self._valid_slot(slot)
        ]
        formatted_date = self._format_date(selected_date)
        if not choices:
            return self._show_date_options(
                session,
                f"Não encontrei horários para clínico geral em {formatted_date}. Escolha outra data.",
            )
        message = f"{prefix}Encontrei horários para clínico geral em {formatted_date}."
        return self._set_block(session, "AGUARDANDO_HORARIO", "SELECIONAR_HORARIO", "Escolha um horário", choices, message)

    def _show_pet_options(self, session: BookingSession, bearer_token: str) -> BookingFlowResponse:
        try:
            pets = self.java_client.list_pets(bearer_token)
        except JavaVetSyncError as exc:
            raise BookingFlowError("Não consegui consultar seus pets agora. Tente novamente em instantes.") from exc
        choices = [
            BookingOption(
                action="PET",
                data={"idPet": pet["idPet"], "nmPet": pet["nmPet"]},
                label=pet["nmPet"],
                description=pet.get("nmEspecie") or pet.get("especie"),
            )
            for pet in pets
            if pet.get("idPet") is not None and pet.get("nmPet")
        ]
        if not choices:
            raise BookingFlowError("Não encontrei pets cadastrados para concluir este agendamento.")
        return self._set_block(
            session,
            "AGUARDANDO_PET",
            "SELECIONAR_PET",
            "Qual pet será atendido?",
            choices,
            "Agora escolha o pet que será atendido.",
        )

    def _show_confirmation(self, session: BookingSession) -> BookingFlowResponse:
        selected = session.selected
        missing = ("idPet", "idTipoEvento", "idVeterinario", "date", "hrEvento")
        if any(key not in selected for key in missing):
            raise BookingFlowError("Faltam escolhas para confirmar a consulta. Comece novamente.")
        description = (
            f"{selected['nmPet']} · {selected['nmTipoEvento']} · {self._format_date(selected['date'])} "
            f"· {selected['hrEvento']} · {selected['nmVeterinario']}"
        )
        choices = [
            BookingOption("CONFIRM", {}, "Confirmar reserva", description),
            BookingOption("CHANGE_SLOT", {}, "Escolher outro horário"),
        ]
        return self._set_block(
            session,
            "AGUARDANDO_CONFIRMACAO",
            "CONFIRMAR_RESERVA",
            "Confirme os dados da consulta",
            choices,
            "Confira a consulta antes de confirmar.",
        )

    def _confirm(self, session: BookingSession, bearer_token: str) -> BookingFlowResponse:
        selected = session.selected
        payload = {
            "idPet": selected["idPet"],
            "idTipoEvento": selected["idTipoEvento"],
            "idVeterinario": selected["idVeterinario"],
            "dtEvento": selected["date"],
            "hrEvento": selected["hrEvento"],
            "dsObservacao": selected.get("dsObservacao"),
        }
        try:
            event = self.java_client.create_event(bearer_token, payload)
        except JavaVetSyncConflictError:
            session.selected.pop("idPet", None)
            return self._show_general_slots(
                session,
                bearer_token,
                "Esse horário acabou de ficar indisponível. ",
            )
        except JavaVetSyncError as exc:
            raise BookingFlowError("Não consegui confirmar a reserva agora. Nenhuma consulta foi agendada.") from exc

        session.state = "CONCLUIDA"
        session.options.clear()
        event_date = event.get("dtEvento", selected["date"]) if isinstance(event, dict) else selected["date"]
        event_time = event.get("hrEvento", selected["hrEvento"]) if isinstance(event, dict) else selected["hrEvento"]
        event_type = event.get("nmTipoEvento", selected["nmTipoEvento"]) if isinstance(event, dict) else selected["nmTipoEvento"]
        event_vet = event.get("nmVeterinario", selected["nmVeterinario"]) if isinstance(event, dict) else selected["nmVeterinario"]
        return BookingFlowResponse(
            f"Consulta confirmada para {selected['nmPet']}: {event_type} em {self._format_date(event_date)}, às {event_time}, com {event_vet}."
        )

    def _set_block(
        self,
        session: BookingSession,
        state: str,
        block_type: str,
        title: str,
        choices: list[BookingOption],
        message: str,
    ) -> BookingFlowResponse:
        session.state = state
        session.options.clear()
        options = []
        for choice in choices:
            option_id = str(uuid4())
            session.options[option_id] = choice
            option = {"id": option_id, "rotulo": choice.label, "habilitado": True}
            if choice.description:
                option["descricao"] = choice.description
            options.append(option)
        return BookingFlowResponse(message, {
            "tipo": block_type,
            "sessaoId": session.id,
            "titulo": title,
            "opcoes": options,
        })

    @staticmethod
    def _valid_slot(slot: Any) -> bool:
        return isinstance(slot, dict) and all(slot.get(key) is not None for key in (
            "idTipoEvento", "nmTipoEvento", "idVeterinario", "nmVeterinario", "hrEvento"
        ))

    @staticmethod
    def _resolve_date(message: str) -> date | None:
        today = datetime.now(BOOKING_TIMEZONE).date()
        normalized = message.lower()
        if "amanhã" in normalized or "amanha" in normalized:
            return today + timedelta(days=1)
        if "hoje" in normalized:
            return today
        iso_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", message)
        if iso_match:
            try:
                return date.fromisoformat(iso_match.group(1))
            except ValueError:
                return None
        day_match = re.search(r"\bdia\s+([0-3]?\d)\b(?!\s+de\b)", normalized)
        if not day_match:
            return None
        requested_day = int(day_match.group(1))
        year, month = today.year, today.month
        if requested_day < today.day:
            month += 1
            if month == 13:
                year, month = year + 1, 1
        try:
            return date(year, month, requested_day)
        except ValueError:
            return None

    @staticmethod
    def _health_prefix(message: str) -> str:
        health_words = ("dor", "xoxa", "desânimo", "desanimo", "vomit", "ferimento", "queda", "machuc", "febre")
        if any(word in message.lower() for word in health_words):
            return "Como você relatou uma mudança no bem-estar do pet, recomendo avaliação presencial na clínica. "
        return ""

    @staticmethod
    def _format_date(value: str) -> str:
        return date.fromisoformat(value).strftime("%d/%m/%Y")

    @staticmethod
    def _weekday_name(value: date) -> str:
        names = ("segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo")
        return names[value.weekday()]
