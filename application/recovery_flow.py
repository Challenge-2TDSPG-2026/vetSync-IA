"""Acompanhamento conversacional baseado no histórico real do pet.

O fluxo começa por uma escolha explícita do pet e guarda somente os dados
necessários para contextualizar a resposta seguinte do tutor. Nenhum estado de
saúde é presumido antes de o tutor descrevê-lo.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from threading import RLock
from typing import Any
from uuid import uuid4

from application.booking_flow import BOOKING_TIMEZONE, BookingOption
from infrastructure.java_vetsync_client import JavaVetSyncClient, JavaVetSyncError


class RecoveryFlowError(Exception):
    pass


@dataclass
class RecoveryResponse:
    message: str
    block: dict[str, Any] | None = None

    def to_payload(self) -> dict[str, Any]:
        payload = {"mensagem": self.message}
        if self.block:
            payload["bloco"] = self.block
        return payload


@dataclass
class RecoverySession:
    id: str
    tutor_id: str
    expires_at: datetime
    state: str = "AGUARDANDO_PET"
    selected: dict[str, Any] = field(default_factory=dict)
    options: dict[str, BookingOption] = field(default_factory=dict)


class RecoverySessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, RecoverySession] = {}
        self._lock = RLock()

    def create(self, tutor_id: str) -> RecoverySession:
        with self._lock:
            self._cleanup()
            session = RecoverySession(
                id=str(uuid4()),
                tutor_id=tutor_id,
                expires_at=datetime.now(BOOKING_TIMEZONE) + timedelta(minutes=15),
            )
            self._sessions[session.id] = session
            return session

    def get(self, session_id: str, tutor_id: str) -> RecoverySession:
        with self._lock:
            self._cleanup()
            session = self._sessions.get(session_id)
            if not session or session.tutor_id != tutor_id:
                raise RecoveryFlowError("Essa etapa de acompanhamento expirou. Comece novamente para consultar o histórico atual.")
            session.expires_at = datetime.now(BOOKING_TIMEZONE) + timedelta(minutes=15)
            return session

    def active_for(self, tutor_id: str) -> RecoverySession | None:
        with self._lock:
            self._cleanup()
            candidates = [session for session in self._sessions.values()
                          if session.tutor_id == tutor_id and session.state == "AGUARDANDO_RELATO"]
            if not candidates:
                return None
            session = max(candidates, key=lambda item: item.expires_at)
            session.expires_at = datetime.now(BOOKING_TIMEZONE) + timedelta(minutes=15)
            return session

    def _cleanup(self) -> None:
        now = datetime.now(BOOKING_TIMEZONE)
        for session_id in [key for key, value in self._sessions.items() if value.expires_at <= now]:
            del self._sessions[session_id]


class RecoveryFlowService:
    """Fluxo de acompanhamento sem inferir diagnóstico ou melhora clínica."""

    def __init__(self, java_client: JavaVetSyncClient, sessions: RecoverySessionStore | None = None) -> None:
        self.java_client = java_client
        self.sessions = sessions or RecoverySessionStore()

    def start(self, tutor_id: str, bearer_token: str) -> RecoveryResponse:
        session = self.sessions.create(tutor_id)
        try:
            pets = self.java_client.list_pets(bearer_token)
        except JavaVetSyncError as exc:
            raise RecoveryFlowError("Não consegui consultar seus pets agora. Tente novamente em instantes.") from exc

        options = [
            BookingOption(
                action="PET",
                data={"idPet": pet["idPet"], "nmPet": pet["nmPet"]},
                label=pet["nmPet"],
                description=pet.get("nmEspecie") or pet.get("especie"),
            )
            for pet in pets
            if pet.get("idPet") is not None and pet.get("nmPet")
        ]
        if not options:
            raise RecoveryFlowError("Não encontrei pets cadastrados para iniciar o acompanhamento.")
        return self._set_block(
            session,
            "AGUARDANDO_PET",
            "SELECIONAR_PET_ACOMPANHAMENTO",
            "Qual pet você quer acompanhar?",
            options,
            "Claro. Qual pet você quer acompanhar?",
        )

    def select(self, session_id: str, option_id: str, tutor_id: str, bearer_token: str) -> RecoveryResponse:
        session = self.sessions.get(session_id, tutor_id)
        option = session.options.get(option_id)
        if not option or option.action != "PET":
            raise RecoveryFlowError("Essa opção não é mais válida. Escolha um dos pets exibidos.")

        session.selected.update(option.data)
        try:
            events = self.java_client.list_events(bearer_token)
        except JavaVetSyncError as exc:
            raise RecoveryFlowError("Não consegui consultar o histórico desse pet agora. Tente novamente em instantes.") from exc

        pet_events = [event for event in events if self._same_pet(event.get("idPet"), option.data["idPet"])]
        latest = self._latest_completed_event(pet_events)
        upcoming_return = self._upcoming_return(pet_events)
        session.selected["latest_event"] = latest
        session.selected["upcoming_return"] = upcoming_return
        session.state = "AGUARDANDO_RELATO"
        session.options.clear()
        return RecoveryResponse(self._question_for(session))

    def respond_to_report(self, tutor_id: str, report: str) -> RecoveryResponse | None:
        session = self.sessions.active_for(tutor_id)
        if not session:
            return None
        normalized = self._normalize(report)
        if self._indicates_not_better(normalized):
            session.state = "CONCLUIDA"
            return RecoveryResponse(self._not_better_message(session))
        if self._indicates_better(normalized):
            session.state = "CONCLUIDA"
            return RecoveryResponse(self._better_message(session))
        return RecoveryResponse(self._clarify_message(session))

    def _set_block(
        self,
        session: RecoverySession,
        state: str,
        block_type: str,
        title: str,
        choices: list[BookingOption],
        message: str,
    ) -> RecoveryResponse:
        session.state = state
        session.options.clear()
        options = []
        for choice in choices:
            option_id = str(uuid4())
            session.options[option_id] = choice
            item = {"id": option_id, "rotulo": choice.label, "habilitado": True}
            if choice.description:
                item["descricao"] = choice.description
            options.append(item)
        return RecoveryResponse(message, {
            "tipo": block_type,
            "sessaoId": session.id,
            "titulo": title,
            "opcoes": options,
        })

    @staticmethod
    def _same_pet(left: Any, right: Any) -> bool:
        return str(left) == str(right)

    @staticmethod
    def _event_date(event: dict[str, Any]) -> date | None:
        raw_date = event.get("dtEvento")
        try:
            return date.fromisoformat(str(raw_date))
        except (TypeError, ValueError):
            return None

    def _latest_completed_event(self, events: list[dict[str, Any]]) -> dict[str, Any] | None:
        completed = [event for event in events if str(event.get("status", "")).upper() == "CONCLUIDO"
                     and self._event_date(event) and self._is_recovery_reference(event)]
        return max(completed, key=lambda event: self._event_date(event) or date.min, default=None)

    def _upcoming_return(self, events: list[dict[str, Any]]) -> dict[str, Any] | None:
        today = datetime.now(BOOKING_TIMEZONE).date()
        returns = [
            event for event in events
            if str(event.get("status", "")).upper() == "AGENDADO"
            and self._event_date(event) is not None
            and (self._event_date(event) or today) >= today
            and "retorno" in self._normalize(str(event.get("nmTipoEvento", "")))
        ]
        return min(returns, key=lambda event: self._event_date(event) or date.max, default=None)

    def _is_recovery_reference(self, event: dict[str, Any]) -> bool:
        source = f"{event.get('nmTipoEvento', '')} {event.get('dsCategoria', '')}"
        normalized = self._normalize(source)
        return any(term in normalized for term in ("consulta", "clinico", "cirurg", "exame", "retorno"))

    def _question_for(self, session: RecoverySession) -> str:
        pet = session.selected["nmPet"]
        latest = session.selected.get("latest_event")
        if not latest:
            return (
                f"Não encontrei um atendimento concluído de {pet} para usar como referência. "
                "Como ele está hoje?"
            )
        event_type = latest.get("nmTipoEvento") or "atendimento"
        event_date = self._format_date(latest.get("dtEvento"))
        professional = latest.get("nmVeterinario") or latest.get("nmProfissionalEstetica")
        clinic = latest.get("nmClinica")
        place = self._place(professional, clinic)
        detail = self._event_detail(latest)
        focus = self._focus_question(detail)
        message = f"O último atendimento concluído de {pet} foi {event_type} em {event_date}{place}."
        if detail:
            message += f" No registro consta: {detail}."
        message += f" {focus}"
        return f"{message}{self._upcoming_return_message(session.selected.get('upcoming_return'))}"

    def _better_message(self, session: RecoverySession) -> str:
        pet = session.selected["nmPet"]
        message = f"Que bom saber que {pet} parece estar melhor. Ainda assim, não consigo confirmar a evolução clínica pelo chat."
        upcoming = session.selected.get("upcoming_return")
        if upcoming:
            message += self._upcoming_return_message(upcoming)
            return message + " Se surgir alguma preocupação antes desse retorno, posso ajudar a marcar uma avaliação presencial."
        return message + " Se quiser, posso ajudar a marcar um retorno presencial."

    def _not_better_message(self, session: RecoverySession) -> str:
        pet = session.selected["nmPet"]
        latest = session.selected.get("latest_event") or {}
        place = self._place(latest.get("nmVeterinario") or latest.get("nmProfissionalEstetica"), latest.get("nmClinica"))
        message = f"Sinto que {pet} ainda não esteja melhor. Como a queixa persiste, recomendo levá-lo para uma avaliação presencial"
        if place:
            message += place
        message += "."
        upcoming = session.selected.get("upcoming_return")
        if upcoming:
            message += self._upcoming_return_message(upcoming)
            return message + " Se estiver preocupado antes dessa data, posso ajudar a marcar outro atendimento."
        return message + " Se quiser, posso ajudar a marcar uma consulta."

    def _clarify_message(self, session: RecoverySession) -> str:
        pet = session.selected["nmPet"]
        return (
            f"Entendi. Para eu orientar o próximo passo para {pet}, ele parece estar melhor, igual ou pior desde esse atendimento? "
            "Não consigo avaliar clinicamente pelo chat."
        )

    def _upcoming_return_message(self, event: dict[str, Any] | None) -> str:
        if not event:
            return ""
        event_date = self._event_date(event)
        if not event_date:
            return ""
        days = (event_date - datetime.now(BOOKING_TIMEZONE).date()).days
        when = "hoje" if days == 0 else f"daqui a {days} dia" + ("s" if days != 1 else "")
        time = f" às {event['hrEvento']}" if event.get("hrEvento") else ""
        place = self._place(event.get("nmVeterinario") or event.get("nmProfissionalEstetica"), event.get("nmClinica"))
        return f" Há um retorno agendado para {self._format_date(event.get('dtEvento'))}{time}, {when}{place}."

    @staticmethod
    def _place(professional: Any, clinic: Any) -> str:
        parts = []
        if professional:
            parts.append(f"com {professional}")
        if clinic:
            parts.append(f"na {clinic}")
        return " " + " ".join(parts) if parts else ""

    @staticmethod
    def _event_detail(event: dict[str, Any]) -> str | None:
        for key in ("observacaoClinica", "diagnostico", "conduta", "dsObservacao", "observacaoTutor"):
            value = event.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    def _focus_question(self, detail: str | None) -> str:
        normalized = self._normalize(detail or "")
        if "manc" in normalized:
            return "Ele ainda está mancando?"
        if "vomit" in normalized:
            return "Ele ainda apresentou vômitos?"
        if "diarre" in normalized:
            return "Ele ainda está com diarreia?"
        if any(word in normalized for word in ("cirurg", "incis", "ponto")):
            return "Como ele está desde o procedimento?"
        if detail:
            return "Como ele está desde esse atendimento?"
        return "Como ele está desde então?"

    @staticmethod
    def _normalize(value: str) -> str:
        replacements = str.maketrans("áàãâéêíóôõúç", "aaaaeeiooouc")
        return value.lower().translate(replacements)

    def _indicates_not_better(self, text: str) -> bool:
        negative = ("nao melhor", "não melhor", "continua", "pior", "igual", "ainda manca", "ainda esta", "ainda está", "nao passou", "não passou")
        return any(term in text for term in negative)

    def _indicates_better(self, text: str) -> bool:
        positive = ("melhor", "bem", "normal", "recuper", "parou", "sumiu")
        return any(term in text for term in positive)

    @staticmethod
    def _format_date(raw: Any) -> str:
        try:
            return date.fromisoformat(str(raw)).strftime("%d/%m/%Y")
        except (TypeError, ValueError):
            return str(raw or "data não informada")
