from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from infrastructure.database.connection import get_db
from infrastructure.auth.security import verificar_token_externo
from application.ports import IAssistantGateway
from infrastructure.gemini_gateway import GeminiGateway
from application.use_cases import ProcessCheckinIntentUseCase
from domain.models import CheckinResult

router = APIRouter(
    prefix="/api/v1/ia/checkins",
    tags=["Check-in Pós-Cirúrgico (IA + Oracle)"]
)

class MensagemCheckinRequest(BaseModel):
    message: str
    surgery_id: Optional[str] = None
    days_post_surgery: Optional[int] = None

def get_checkin_use_case() -> ProcessCheckinIntentUseCase:
    gateway = GeminiGateway()
    return ProcessCheckinIntentUseCase(gateway=gateway)

@router.post("/processar")
def processar_checkin(
    request: MensagemCheckinRequest,
    usuario_logado: dict = Depends(verificar_token_externo),
    db: Session = Depends(get_db),
    use_case: ProcessCheckinIntentUseCase = Depends(get_checkin_use_case)
):
    """
    Recebe os relatos do tutor sobre recuperação, extrai o status e red flags,
    e grava a linha do tempo no Oracle.
    """
    context = {}
    if request.surgery_id: context["surgery_id"] = request.surgery_id
    if request.days_post_surgery: context["days_post_surgery"] = request.days_post_surgery

    try:
        ia_result: CheckinResult = use_case.execute(request.message, context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na IA: {str(e)}")

    from infrastructure.database.models import Checkin
    import json
    
    checkin_historico = Checkin(
        tutor_id=usuario_logado["username"],
        recovery_status=ia_result.recovery_status, 
        surgery_id=request.surgery_id,
        red_flags=json.dumps(ia_result.red_flags),
        notify_veterinarian=ia_result.notify_veterinarian
    )
    db.add(checkin_historico)
    db.commit()

    return {
        "usuario_logado": usuario_logado["username"],
        "dados_ia": ia_result,
        "status_banco": "Ação pendente de implementação no banco"
    }
