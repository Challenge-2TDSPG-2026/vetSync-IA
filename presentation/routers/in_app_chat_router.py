from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from infrastructure.database.connection import get_db
from infrastructure.database.models import MensagemChat
from infrastructure.gemini_gateway import GeminiGateway

router = APIRouter(prefix="/api/v1/in-app", tags=["In-App Chat Workflow"])

class DoctorRequest(BaseModel):
    comando: str
    tutor_id: str

class TutorRequest(BaseModel):
    mensagem: str
    tutor_id: str

@router.post("/doctor/comando")
def doctor_command(req: DoctorRequest, db: Session = Depends(get_db)):
    gateway = GeminiGateway()
    # Process the doctor's command
    result = gateway.parse_doctor_command(req.comando)
    
    # If the doctor asked to send a message to the tutor
    if result.get("action") == "ENVIAR_MENSAGEM" and result.get("message_draft"):
        nova_msg = MensagemChat(
            tutor_id=req.tutor_id,
            remetente="IA",
            texto=result["message_draft"]
        )
        db.add(nova_msg)
        db.commit()
    
    return {"status": "success", "ia_response": result}

@router.get("/chat/{tutor_id}")
def get_chat_history(tutor_id: str, db: Session = Depends(get_db)):
    mensagens = db.query(MensagemChat).filter(MensagemChat.tutor_id == tutor_id).order_by(MensagemChat.created_at.asc()).all()
    return {"mensagens": mensagens}

@router.post("/chat/tutor")
def tutor_reply(req: TutorRequest, db: Session = Depends(get_db)):
    # Save the tutor's message
    nova_msg_tutor = MensagemChat(
        tutor_id=req.tutor_id,
        remetente="TUTOR",
        texto=req.mensagem
    )
    db.add(nova_msg_tutor)
    db.commit()

    # Load history to give context to the AI
    mensagens = db.query(MensagemChat).filter(MensagemChat.tutor_id == req.tutor_id).order_by(MensagemChat.created_at.asc()).all()
    history_context = []
    for m in mensagens:
        role = "user" if m.remetente == "TUTOR" else "assistant"
        history_context.append({"role": role, "text": m.texto})
    
    # Let AI negotiate the schedule
    gateway = GeminiGateway()
    context = {"history": history_context, "tutor_id": req.tutor_id}
    intent = gateway.parse_scheduling_intent(req.mensagem, context=context)

    # Save the AI's response
    if intent.message_draft:
        nova_msg_ia = MensagemChat(
            tutor_id=req.tutor_id,
            remetente="IA",
            texto=intent.message_draft
        )
        db.add(nova_msg_ia)
        db.commit()
        return {"status": "success", "ia_reply": intent.message_draft, "intent": intent.dict()}
    
    return {"status": "success", "intent": intent.dict()}

