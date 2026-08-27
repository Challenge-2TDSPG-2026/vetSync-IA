from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from infrastructure.database.connection import get_db
from infrastructure.auth.security import verificar_token_externo
from infrastructure.gemini_gateway import GeminiGateway
from application.use_cases import ProcessOrchestratorIntentUseCase

# Import the actual routers to redirect to their specific use cases
from application.use_cases import (
    ProcessSchedulingIntentUseCase,
    ProcessPostCareIntentUseCase,
    ProcessTriageIntentUseCase,
    ProcessCheckinIntentUseCase
)

router = APIRouter(
    prefix="/api/v1/ia/orquestrador",
    tags=["Orquestrador (Chat)"]
)

class MensagemChatRequest(BaseModel):
    message: str
    contexto: Optional[dict] = None

def get_orchestrator_use_case() -> ProcessOrchestratorIntentUseCase:
    gateway = GeminiGateway()
    return ProcessOrchestratorIntentUseCase(gateway=gateway)

def get_gemini_gateway() -> GeminiGateway:
    return GeminiGateway()

@router.post("/processar")
def processar_chat_universal(
    request: MensagemChatRequest,
    usuario_logado: dict = Depends(verificar_token_externo),
    db: Session = Depends(get_db),
    use_case: ProcessOrchestratorIntentUseCase = Depends(get_orchestrator_use_case),
    gateway: GeminiGateway = Depends(get_gemini_gateway)
):
    """
    Endpoint de entrada único (Universal).
    Lê a mensagem, usa a IA para classificar a intenção e então redireciona para o UseCase correto.
    """
    try:
        # 1. Enriquecer o contexto com os dados do banco (Simulado aqui, mas em prod viria do Oracle)
        contexto_enriquecido = request.contexto or {}
        contexto_enriquecido["tutor_id"] = usuario_logado["username"]
        contexto_enriquecido["pets_do_tutor"] = ["Thor (Cachorro)", "Nina (Gato)"] # Simulação de busca no banco

        # 2. Orquestração: Descobrir o que o usuário quer
        orquestracao = use_case.execute(request.message)
        categoria = orquestracao.intent_category
        
        resultado_final = None
        
        # 3. Roteamento interno
        if categoria == "AGENDAMENTO":
            uc = ProcessSchedulingIntentUseCase(gateway)
            resultado_final = uc.execute(request.message, contexto_enriquecido)
            # TODO: Lógica de banco de dados para agendamento
            
        elif categoria == "TRIAGEM":
            uc = ProcessTriageIntentUseCase(gateway)
            resultado_final = uc.execute(request.message, contexto_enriquecido)
            # TODO: Lógica de banco de dados para triagem
            
        elif categoria == "POS_ATENDIMENTO":
            uc = ProcessPostCareIntentUseCase(gateway)
            resultado_final = uc.execute(request.message)
            # TODO: Lógica de banco de dados para pós-atendimento
            
        elif categoria == "CHECKIN":
            uc = ProcessCheckinIntentUseCase(gateway)
            resultado_final = uc.execute(request.message, contexto_enriquecido)
            # TODO: Lógica de banco de dados para checkin
            
        else:
            # Caso "OUTRO"
            return {
                "categoria": categoria,
                "motivo": orquestracao.reasoning,
                "mensagem": "Desculpe, só posso ajudar com assuntos relacionados à clínica veterinária (agendamentos, triagem, etc)."
            }
            
        return {
            "usuario_logado": usuario_logado["username"],
            "categoria_identificada": categoria,
            "dados_ia": resultado_final,
            "status_banco": "Ação de banco pendente de implementação no orquestrador"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no orquestrador: {str(e)}")
