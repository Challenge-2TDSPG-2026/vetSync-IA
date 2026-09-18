from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from infrastructure.auth.security import verificar_token_externo
from infrastructure.gemini_gateway import GeminiGateway

router = APIRouter(
    prefix="/api/v1/ia/orquestrador",
    tags=["Orquestrador (Chat)"]
)

class MensagemChatRequest(BaseModel):
    message: str
    contexto: Optional[dict] = None

def get_gemini_gateway() -> GeminiGateway:
    return GeminiGateway()

@router.post("/processar")
def processar_chat_universal(
    request: MensagemChatRequest,
    usuario_logado: dict = Depends(verificar_token_externo),
    gateway: GeminiGateway = Depends(get_gemini_gateway)
):
    """
    Entrada conversacional da SIA para o tutor.
    Não expõe nem executa classificação de triagem, urgência ou intenção.
    """
    try:
        # Preserva somente o contexto recebido e associa a conversa ao tutor autenticado.
        contexto_enriquecido = dict(request.contexto or {})
        contexto_enriquecido["tutor_id"] = usuario_logado["username"]
        mensagem = gateway.responder_ao_tutor(request.message, contexto_enriquecido)
        return {"mensagem": mensagem}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no orquestrador: {str(e)}")
