"""Preparação e leitura pós-consulta com dados autorizados pelo backend Java."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from zoneinfo import ZoneInfo

from application.ports import AssistantGatewayError
from infrastructure.auth.security import verificar_token_externo
from infrastructure.gemini_gateway import GeminiGateway
from infrastructure.java_vetsync_client import JavaVetSyncClient, JavaVetSyncError, JavaVetSyncAccessError
from presentation.routers.orquestrador_router import get_gemini_gateway, get_java_vetsync_client

router = APIRouter(prefix="/api/v1/ia/jornada", tags=["Jornada SIA"])


class PrepararRequest(BaseModel):
    petId: int = Field(gt=0)
    relato: str = Field(min_length=10, max_length=4000)


class PosConsultaRequest(BaseModel):
    petId: int = Field(gt=0)
    eventoId: int = Field(gt=0)


@router.post("/preparar")
def preparar(
    request: PrepararRequest,
    usuario: dict = Depends(verificar_token_externo),
    java: JavaVetSyncClient = Depends(get_java_vetsync_client),
    gemini: GeminiGateway | None = Depends(get_gemini_gateway),
):
    try:
        pet = next((item for item in java.list_pets(usuario["token"])
                    if item.get("idPet") == request.petId), None)
        if pet is None:
            raise HTTPException(status_code=404, detail="Pet não encontrado na sua conta.")
        if gemini is None:
            raise AssistantGatewayError("Gerador de resumo indisponível")
        draft = gemini.preparar_consulta(request.relato, pet.get("nmPet") or "pet")
        return {"petId": request.petId, "origem": "IA_RASCUNHO", **draft}
    except HTTPException:
        raise
    except JavaVetSyncAccessError as exc:
        raise HTTPException(status_code=403, detail="Você não tem acesso a este pet.") from exc
    except JavaVetSyncError as exc:
        raise HTTPException(status_code=503, detail="Não consegui validar o acesso ao pet agora.") from exc
    except AssistantGatewayError as exc:
        raise HTTPException(status_code=503, detail="Não consegui preparar o resumo agora.") from exc


@router.post("/pos-consulta")
def pos_consulta(
    request: PosConsultaRequest,
    usuario: dict = Depends(verificar_token_externo),
    java: JavaVetSyncClient = Depends(get_java_vetsync_client),
):
    """Organiza literalmente registros do profissional, sem gerar nova conduta."""
    try:
        if not any(item.get("idPet") == request.petId for item in java.list_pets(usuario["token"])):
            raise HTTPException(status_code=404, detail="Pet não encontrado na sua conta.")
        event = java.get_event_details(usuario["token"], request.eventoId)
        if not isinstance(event, dict) or event.get("idPet") != request.petId:
            raise HTTPException(status_code=404, detail="Atendimento não encontrado para este pet.")
        record = java.get_record(usuario["token"], request.petId)
        orientations = [
            {"id": item["id"], "titulo": item["titulo"], "texto": item["texto"], "autor": item.get("autor")}
            for item in record.get("orientacoes", [])
            if item.get("eventoId") == request.eventoId
        ]
        prescriptions = [
            {"id": item["id"], "medicamento": item["medicamento"], "posologia": item["posologia"],
             "inicio": item.get("inicio"), "fim": item.get("fim")}
            for item in record.get("receitas", [])
            if item.get("eventoId") == request.eventoId and item.get("status") == "LIBERADO"
        ]
        today = datetime.now(ZoneInfo("America/Sao_Paulo")).date().isoformat()
        upcoming = [
            {"id": item["idEvento"], "tipo": item.get("nmTipoEvento"),
             "data": item.get("dtEvento"), "hora": item.get("hrEvento")}
            for item in java.list_events(usuario["token"])
            if item.get("idPet") == request.petId and item.get("status") == "AGENDADO"
            and isinstance(item.get("dtEvento"), str) and item["dtEvento"] >= today
        ]
        plans = [
            {"id": item["idPlano"], "veterinario": item.get("nmVeterinario"), "itens": item.get("itens", [])}
            for item in java.get_pet_plans(usuario["token"], request.petId)
            if item.get("status") == "EM_ANDAMENTO"
        ]
        return {
            "eventoId": request.eventoId,
            "origem": "REGISTROS_VETERINARIOS",
            "orientacoes": orientations,
            "medicamentos": prescriptions,
            "proximosAgendamentos": upcoming,
            "planosAtivos": plans,
            "mensagem": (
                "Organizei abaixo apenas as orientações e receitas liberadas registradas para este atendimento. "
                "Em caso de dúvida, confirme com o veterinário."
            ) if orientations or prescriptions else (
                "Ainda não encontrei orientações ou receitas liberadas para este atendimento. "
                "Consulte o veterinário antes de iniciar ou alterar qualquer cuidado."
            ),
        }
    except HTTPException:
        raise
    except JavaVetSyncAccessError as exc:
        raise HTTPException(status_code=403, detail="Você não tem acesso a este atendimento.") from exc
    except JavaVetSyncError as exc:
        raise HTTPException(status_code=503, detail="Não consegui consultar os registros do atendimento agora.") from exc
