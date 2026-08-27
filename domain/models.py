from pydantic import BaseModel, Field
from typing import Optional

class ConversationMessage(BaseModel):
    role: str = Field(description="O papel do autor da mensagem: 'user' ou 'assistant'")
    text: str = Field(description="O conteúdo da mensagem")

class ClinicalPostCarePlan(BaseModel):
    pet_name: Optional[str] = Field(description="Nome do pet, se mencionado.")
    tutor_name: Optional[str] = Field(description="Nome do tutor, se mencionado.")
    days_until_follow_up: Optional[int] = Field(description="Dias até o próximo retorno, se aplicável.")
    follow_up_reason: Optional[str] = Field(description="Motivo do retorno ou recomendação de acompanhamento.")
    attach_prescription: bool = Field(description="Verdadeiro se houver necessidade de anexar receita.")
    attach_medical_record: bool = Field(description="Verdadeiro se houver necessidade de anexar prontuário.")
    message_draft: str = Field(description="Rascunho da mensagem que será enviada ao tutor via WhatsApp ou e-mail, em tom amigável e profissional, focado no pós-atendimento veterinário.")

class SchedulingIntent(BaseModel):
    action: str = Field(description="Ação interpretada: CONSULTAR, RESERVAR, CONFIRMAR, CANCELAR, REAGENDAR, OPCOES_TUTOR, SAUDACAO, ASSUNTO_INVALIDO")
    date_reference: Optional[str] = Field(description="Referência de data mencionada ou calculada")
    time_reference: Optional[str] = Field(description="Referência de horário mencionado")
    doctor_name: Optional[str] = Field(description="Nome do doutor responsável, se mencionado")
    patient_name: Optional[str] = Field(description="Nome do paciente, se mencionado")
    state: Optional[str] = Field(description="Estado sugerido do agendamento (PENDENTE_DOUTOR, CONFIRMADO_DOUTOR, AGUARDANDO_TUTOR, etc.)")
    message_draft: str = Field(description="Resposta sugerida da IA para o doutor ou tutor")

class TriageInboundRequest(BaseModel):
    message: str
    history: Optional[list[ConversationMessage]] = None
    pet_id: Optional[str] = None
    tutor_id: Optional[str] = None
    clinic_id: Optional[str] = None
    conversation_id: Optional[str] = None
    patient_species: Optional[str] = None
    patient_name: Optional[str] = None

class TriageResult(BaseModel):
    urgency_level: str = Field(description="Nível de urgência: EMERGENCIA, URGENCIA, ROTINA, ADMINISTRATIVO")
    identified_symptoms: list[str] = Field(description="Lista de sintomas extraídos")
    suggested_action: str = Field(description="Próximo passo operacional da clínica")
    auto_reply_draft: str = Field(description="Rascunho de mensagem para o tutor")
    notify_team: bool = Field(description="Verdadeiro se a equipe precisar ser notificada (ex: emergência)")

class CheckinResponseRequest(BaseModel):
    message: str
    history: Optional[list[ConversationMessage]] = None
    pet_id: Optional[str] = None
    tutor_id: Optional[str] = None
    clinic_id: Optional[str] = None
    veterinarian_id: Optional[str] = None
    surgery_id: Optional[str] = None
    days_post_surgery: Optional[int] = None
    conversation_id: Optional[str] = None

class CheckinResult(BaseModel):
    recovery_status: str = Field(description="Estado da recuperação: NORMAL, ALERTA_MODERADO, COMPLICACAO_CRITICA")
    red_flags: list[str] = Field(description="Sinais de complicação identificados")
    notify_veterinarian: bool = Field(description="Verdadeiro se o veterinário deve ser notificado")
    message_draft: str = Field(description="Rascunho de mensagem para o tutor")

class OrchestratorResult(BaseModel):
    intent_category: str = Field(description="A categoria da intenção: AGENDAMENTO, TRIAGEM, POS_ATENDIMENTO, CHECKIN, ou OUTRO")
    reasoning: str = Field(description="O motivo da classificação")
