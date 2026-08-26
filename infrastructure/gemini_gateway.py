import os
import json
from google import genai
from google.genai import types
from domain.models import ClinicalPostCarePlan, SchedulingIntent, TriageResult, CheckinResult
from infrastructure.prompts import SCHEDULE_SYSTEM_INSTRUCTION, TRIAGE_SYSTEM_INSTRUCTION, CHECKIN_SYSTEM_INSTRUCTION
from application.ports import IAssistantGateway, AssistantGatewayError

class GeminiGateway(IAssistantGateway):
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise AssistantGatewayError("GEMINI_API_KEY environment variable is missing.")
        
        self.client = genai.Client(api_key=api_key)
        self.model_id = 'gemini-3.6-flash'
        
        self.system_instruction = (
            "Seu nome é SIA (Sync Inteligência Artificial), a assistente virtual do sistema VetSync. "
            "Você é especializada em rotina clínica veterinária. "
            "Sua tarefa é receber comandos em linguagem natural de veterinários "
            "sobre o pós-atendimento de pacientes (pets) e extrair os dados "
            "estruturados para um sistema. Interprete os comandos e retorne um JSON "
            "seguindo o schema fornecido. Seja amigável e profissional no rascunho da mensagem. "
            "Se o usuário enviar apenas uma saudação, responda educadamente. "
            "Se o usuário perguntar sobre assuntos fora do contexto veterinário (ex: clima, notícias), "
            "diga de forma curta e direta que você só pode ajudar com a rotina e o pós-atendimento da clínica. Não fique repetindo seu nome (ex: 'Olá, sou a SIA...') ao negar uma resposta; seja natural e breve."
        )

    def parse_intent(self, prompt: str) -> ClinicalPostCarePlan:
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    response_mime_type="application/json",
                    response_schema=ClinicalPostCarePlan,
                    temperature=0.2,
                )
            )
            
            if not response.text:
                raise AssistantGatewayError("API returned empty text.")
                
            data = json.loads(response.text)
            return ClinicalPostCarePlan(**data)
            
        except Exception as e:
            raise AssistantGatewayError(f"Erro ao processar intent no Gemini: {str(e)}")

    def parse_scheduling_intent(self, prompt: str) -> SchedulingIntent:
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SCHEDULE_SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    response_schema=SchedulingIntent,
                    temperature=0.2,
                )
            )
            
            if not response.text:
                raise AssistantGatewayError("API returned empty text for scheduling.")
                
            data = json.loads(response.text)
            return SchedulingIntent(**data)
            
        except Exception as e:
            raise AssistantGatewayError(f"Erro ao processar intent de agendamento no Gemini: {str(e)}")

    def parse_triage_intent(self, prompt: str, context: dict = None) -> TriageResult:
        try:
            full_prompt = f"Contexto opcional: {json.dumps(context)}\n\nMensagem do tutor: {prompt}" if context else prompt
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=TRIAGE_SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    response_schema=TriageResult,
                    temperature=0.2,
                )
            )
            
            if not response.text:
                raise AssistantGatewayError("API returned empty text for triage.")
                
            data = json.loads(response.text)
            return TriageResult(**data)
            
        except Exception as e:
            raise AssistantGatewayError(f"Erro ao processar intent de triagem no Gemini: {str(e)}")

    def parse_checkin_intent(self, prompt: str, context: dict = None) -> CheckinResult:
        try:
            full_prompt = f"Contexto opcional: {json.dumps(context)}\n\nMensagem do tutor: {prompt}" if context else prompt
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=CHECKIN_SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    response_schema=CheckinResult,
                    temperature=0.2,
                )
            )
            
            if not response.text:
                raise AssistantGatewayError("API returned empty text for checkin.")
                
            data = json.loads(response.text)
            return CheckinResult(**data)
            
        except Exception as e:
            raise AssistantGatewayError(f"Erro ao processar intent de checkin no Gemini: {str(e)}")
