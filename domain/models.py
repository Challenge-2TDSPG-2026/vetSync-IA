from pydantic import BaseModel, Field
from typing import Optional

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
