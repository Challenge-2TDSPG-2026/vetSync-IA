from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from infrastructure.database.connection import get_db
from infrastructure.auth.security import verificar_token_externo
from application.ports import IAssistantGateway
from infrastructure.gemini_gateway import GeminiGateway
from application.use_cases import ProcessSchedulingIntentUseCase
from domain.models.models import SchedulingIntent

router = APIRouter(
    prefix="/api/v1/ia/agendamentos",
    tags=["Agendamentos (IA + Oracle)"]
)

class MensagemChatRequest(BaseModel):
    prompt: str

# Dependência para instanciar a IA
def get_scheduling_use_case() -> ProcessSchedulingIntentUseCase:
    gateway = GeminiGateway()
    return ProcessSchedulingIntentUseCase(gateway=gateway)

@router.post("/processar")
def processar_agendamento(
    request: MensagemChatRequest,
    usuario_logado: dict = Depends(verificar_token_externo),
    db: Session = Depends(get_db),
    use_case: ProcessSchedulingIntentUseCase = Depends(get_scheduling_use_case)
):
    """
    Recebe uma mensagem em texto livre do tutor, passa pela IA para estruturar,
    e automaticamente toma a ação no banco de dados Oracle.
    """
    # 1. Manda a mensagem pra IA (Gemini)
    try:
        ia_result: SchedulingIntent = use_case.execute(request.prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na IA: {str(e)}")

    # 2. Toma a decisão baseada na intenção identificada pela IA
    acao = ia_result.action # Pode ser RESERVAR, CANCELAR, CONFIRMAR, CONSULTAR

    if acao == "RESERVAR" or acao == "REAGENDAR":
        from infrastructure.database.models import Agendamento
        novo_agendamento = Agendamento(
            tutor_id=usuario_logado["username"],
            patient_name=ia_result.patient_name,
            doctor_name=ia_result.doctor_name,
            date_reference=ia_result.date_reference,
            time_reference=ia_result.time_reference,
            state="PENDENTE" if acao == "RESERVAR" else "REAGENDADO"
        )
        db.add(novo_agendamento)
        db.commit()
    elif acao == "CANCELAR":
        # Simula um cancelamento (num sistema real, buscaria o ID do agendamento)
        pass
    
    # 3. Retorna a resposta estruturada para o Frontend (incluindo o texto que a IA sugeriu de resposta)
    return {
        "usuario_logado": usuario_logado["username"],
        "intencao_detectada": acao,
        "dados_ia": ia_result,
        "status_banco": "Ação pendente de implementação no banco"
    }
