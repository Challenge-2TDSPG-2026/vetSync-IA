from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from infrastructure.database.connection import get_db
from infrastructure.auth.security import verificar_token_externo
from application.ports import IAssistantGateway
from infrastructure.gemini_gateway import GeminiGateway
from application.use_cases import ProcessTriageIntentUseCase
from domain.models import TriageResult

router = APIRouter(
    prefix="/api/v1/ia/triagens",
    tags=["Triagem (IA + Oracle)"]
)

class MensagemTriagemRequest(BaseModel):
    message: str
    pet_id: Optional[str] = None
    patient_species: Optional[str] = None

def get_triage_use_case() -> ProcessTriageIntentUseCase:
    gateway = GeminiGateway()
    return ProcessTriageIntentUseCase(gateway=gateway)

@router.post("/processar")
def processar_triagem(
    request: MensagemTriagemRequest,
    usuario_logado: dict = Depends(verificar_token_externo),
    db: Session = Depends(get_db),
    use_case: ProcessTriageIntentUseCase = Depends(get_triage_use_case)
):
    """
    Recebe os sintomas descritos pelo tutor, a IA classifica o risco,
    salva a triagem no Oracle e notifica se for emergência.
    """
    context = {}
    if request.pet_id: context["pet_id"] = request.pet_id
    if request.patient_species: context["patient_species"] = request.patient_species

    try:
        ia_result: TriageResult = use_case.execute(request.message, context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na IA: {str(e)}")

    from infrastructure.database.models import Triagem
    import json
    
    nova_triagem = Triagem(
        urgency_level=ia_result.urgency_level, 
        tutor_id=usuario_logado["username"],
        pet_id=request.pet_id,
        symptoms=json.dumps(ia_result.identified_symptoms),
        notify_team=ia_result.notify_team
    )
    db.add(nova_triagem)
    db.commit()

    return {
        "usuario_logado": usuario_logado["username"],
        "dados_ia": ia_result,
        "status_banco": "Ação pendente de implementação no banco"
    }
