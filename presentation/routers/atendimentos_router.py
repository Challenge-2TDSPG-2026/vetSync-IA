from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from infrastructure.database.connection import get_db
from infrastructure.auth.security import verificar_token_externo
from application.ports import IAssistantGateway
from infrastructure.gemini_gateway import GeminiGateway
from application.use_cases import ProcessPostCareIntentUseCase
from domain.models import ClinicalPostCarePlan

router = APIRouter(
    prefix="/api/v1/ia/atendimentos",
    tags=["Pós-Atendimento (IA + Oracle)"]
)

class MensagemChatRequest(BaseModel):
    prompt: str

def get_postcare_use_case() -> ProcessPostCareIntentUseCase:
    gateway = GeminiGateway()
    return ProcessPostCareIntentUseCase(gateway=gateway)

@router.post("/processar")
def processar_pos_atendimento(
    request: MensagemChatRequest,
    usuario_logado: dict = Depends(verificar_token_externo),
    db: Session = Depends(get_db),
    use_case: ProcessPostCareIntentUseCase = Depends(get_postcare_use_case)
):
    """
    Recebe instruções médicas do veterinário, a IA estrutura o prontuário 
    e salva as pendências ou retornos no Oracle.
    """
    try:
        ia_result: ClinicalPostCarePlan = use_case.execute(request.prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na IA: {str(e)}")

    # TODO: Logica de inserção no banco
    # Exemplo: Atualizar flag do prontuário ou agendar retorno para daqui a X dias
    # if ia_result.days_until_follow_up:
    #     novo_agendamento_retorno = AgendamentoOracle(...)
    #     db.add(novo_agendamento_retorno)
    
    return {
        "usuario_logado": usuario_logado["username"],
        "dados_ia": ia_result,
        "status_banco": "Ação pendente de implementação no banco"
    }
