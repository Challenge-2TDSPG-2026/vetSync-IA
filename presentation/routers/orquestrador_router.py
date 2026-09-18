import re
from calendar import monthrange
from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from infrastructure.auth.security import verificar_token_externo
from infrastructure.gemini_gateway import GeminiGateway
from infrastructure.java_vetsync_client import (
    JavaVetSyncClient,
    JavaVetSyncConflictError,
    JavaVetSyncError,
)

router = APIRouter(
    prefix="/api/v1/ia/orquestrador",
    tags=["Orquestrador (Chat)"]
)

class MensagemChatRequest(BaseModel):
    message: str
    contexto: Optional[dict] = None

def get_gemini_gateway() -> GeminiGateway:
    return GeminiGateway()


def get_java_vetsync_client() -> JavaVetSyncClient:
    return JavaVetSyncClient()


def is_scheduling_turn(message: str, context: dict) -> bool:
    """Reconhece o fluxo sem tentar interpretar ou escolher dados do tutor."""
    conversation = " ".join(
        [message] + [
            item.get("text", "")
            for item in (context.get("history") or [])
            if isinstance(item, dict)
        ]
    ).lower()
    keywords = ("agend", "consulta", "horário", "horario", "marcar", "marca", "reserva")
    return any(keyword in conversation for keyword in keywords)


def validate_event_choice(decision, catalogos: dict) -> dict | None:
    """Não deixa o modelo enviar IDs ou formatos que não vieram do Java."""
    required = (
        decision.id_pet,
        decision.id_tipo_evento,
        decision.id_veterinario,
        decision.dt_evento,
        decision.hr_evento,
    )
    if not all(value is not None for value in required):
        return None

    pet_ids = {item.get("idPet") for item in catalogos.get("pets", [])}
    type_ids = {item.get("idTipoEvento") for item in catalogos.get("tipos_evento", [])}
    vet_ids = {item.get("idVeterinario") for item in catalogos.get("veterinarios", [])}
    if decision.id_pet not in pet_ids or decision.id_tipo_evento not in type_ids or decision.id_veterinario not in vet_ids:
        return None
    try:
        selected_date = date.fromisoformat(decision.dt_evento)
    except (TypeError, ValueError):
        return None
    today = datetime.now(ZoneInfo("America/Sao_Paulo")).date()
    if selected_date < today or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", decision.hr_evento):
        return None
    return {
        "idPet": decision.id_pet,
        "idTipoEvento": decision.id_tipo_evento,
        "idVeterinario": decision.id_veterinario,
        "dtEvento": decision.dt_evento,
        "hrEvento": decision.hr_evento,
        "dsObservacao": decision.ds_observacao,
    }


def normalize_explicit_day(message: str, proposed_date: str | None) -> str | None:
    """Resolve ``dia 20`` de maneira determinística no fuso do produto.

    O modelo ainda entende expressões mais amplas (amanhã, próxima terça etc.),
    mas esta regra evita que um dia do mês informado sem mês/ano fique ambíguo.
    """
    match = re.search(r"\bdia\s+([0-3]?\d)\b(?!\s+de\b)", message, re.IGNORECASE)
    if not match:
        return proposed_date
    requested_day = int(match.group(1))
    today = datetime.now(ZoneInfo("America/Sao_Paulo")).date()
    year, month = today.year, today.month
    if requested_day < today.day:
        month += 1
        if month == 13:
            year, month = year + 1, 1
    if requested_day < 1 or requested_day > monthrange(year, month)[1]:
        return proposed_date
    return date(year, month, requested_day).isoformat()


def confirmation_message(evento: dict, catalogos: dict) -> str:
    raw_date = evento.get("dtEvento", "")
    try:
        formatted_date = date.fromisoformat(raw_date).strftime("%d/%m/%Y")
    except (TypeError, ValueError):
        formatted_date = str(raw_date)
    pets_by_id = {item.get("idPet"): item.get("nmPet") for item in catalogos.get("pets", [])}
    pet = pets_by_id.get(evento.get("idPet")) or "o pet selecionado"
    event_type = evento.get("nmTipoEvento") or "atendimento"
    vet = evento.get("nmVeterinario") or "veterinário selecionado"
    return (
        f"Consulta confirmada para {pet}: {event_type} em {formatted_date}, "
        f"às {evento.get('hrEvento')}, com {vet}."
    )

@router.post("/processar")
def processar_chat_universal(
    request: MensagemChatRequest,
    usuario_logado: dict = Depends(verificar_token_externo),
    gateway: GeminiGateway = Depends(get_gemini_gateway),
    java_client: JavaVetSyncClient = Depends(get_java_vetsync_client),
):
    """
    Entrada conversacional da SIA para o tutor.
    Não expõe nem executa classificação de triagem, urgência ou intenção.
    """
    try:
        # Preserva somente o contexto recebido e associa a conversa ao tutor autenticado.
        contexto_enriquecido = dict(request.contexto or {})
        contexto_enriquecido["tutor_id"] = usuario_logado["username"]

        # Mantém a compatibilidade para gateways de conversa simples e para os
        # testes legados; o Gemini real usa o fluxo estruturado abaixo.
        if not hasattr(gateway, "decidir_agendamento_tutor") or not is_scheduling_turn(request.message, contexto_enriquecido):
            mensagem = gateway.responder_ao_tutor(request.message, contexto_enriquecido)
            return {"mensagem": mensagem}

        try:
            catalogos = java_client.scheduling_context(usuario_logado.get("token", ""))
        except JavaVetSyncError:
            return {
                "mensagem": (
                    "Não consegui consultar os dados da agenda agora. "
                    "Tente novamente em instantes para eu continuar o agendamento."
                )
            }

        contexto_enriquecido["pets_cadastrados"] = catalogos["pets"]
        decision = gateway.decidir_agendamento_tutor(request.message, contexto_enriquecido, catalogos)
        decision.dt_evento = normalize_explicit_day(request.message, decision.dt_evento)
        if not decision.create_event:
            return {"mensagem": decision.message}

        payload = validate_event_choice(decision, catalogos)
        if not payload:
            return {
                "mensagem": (
                    "Para confirmar, preciso da escolha do animal, tipo de atendimento, "
                    "veterinário, data e horário. Qual desses dados falta informar?"
                )
            }
        try:
            evento = java_client.create_event(usuario_logado["token"], payload)
        except JavaVetSyncConflictError:
            return {"mensagem": "Esse horário acabou de ficar indisponível. Escolha outro horário para eu tentar reservar."}
        except JavaVetSyncError:
            return {"mensagem": "Não consegui confirmar a reserva agora. Nenhuma consulta foi agendada; tente novamente em instantes."}

        mensagem = confirmation_message(evento, catalogos)
        return {"mensagem": mensagem}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no orquestrador: {str(e)}")
