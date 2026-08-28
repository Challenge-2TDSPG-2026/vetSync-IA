import os
import json
from google import genai
from google.genai import types
from domain.models.models import ClinicalPostCarePlan, SchedulingIntent, TriageResult, CheckinResult, OrchestratorResult
from infrastructure.prompts import SCHEDULE_SYSTEM_INSTRUCTION, TRIAGE_SYSTEM_INSTRUCTION, CHECKIN_SYSTEM_INSTRUCTION
from application.ports import IAssistantGateway, AssistantGatewayError

class GeminiGateway(IAssistantGateway):
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise AssistantGatewayError("GEMINI_API_KEY environment variable is missing.")
        
        self.client = genai.Client(api_key=api_key)
        self.model_id = 'gemini-3.5-flash-lite' # Modelo mais rápido para evitar gargalo 503
        
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

    def parse_scheduling_intent(self, prompt: str, context: dict = None) -> SchedulingIntent:
        try:
            full_prompt = ""
            if context and "history" in context:
                history = context.pop("history")
                history_text = "\n".join([f"{msg['role'].capitalize()}: {msg['text']}" for msg in history])
                full_prompt += f"Histórico de mensagens:\n{history_text}\n\n"
                
            full_prompt += f"Contexto opcional do tutor/pets: {json.dumps(context)}\n\n" if context else ""

            def consultar_disponibilidade(data_referencia: str) -> list[str]:
                """Consulta a disponibilidade de horários na agenda da clínica para uma determinada data. Ex: 'hoje', 'amanha', '2025-10-10'."""
                print(f"-> [Function Calling] IA consultou a data: {data_referencia}")
                data_lower = data_referencia.lower()
                if "hoje" in data_lower:
                    return ["14:00", "15:30", "17:00"]
                elif "amanh" in data_lower:
                    return ["09:00", "11:00"]
                else:
                    return ["10:00", "13:00", "16:00"]

            # Função auxiliar para retentativas em caso de 503
            import time
            def call_with_retry(func, *args, **kwargs):
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        if "503" in str(e) and attempt < max_retries - 1:
                            time.sleep(2)
                        else:
                            raise e

            # Passo 1: Chat com Function Calling para gerar a resposta textual
            chat = self.client.chats.create(
                model=self.model_id,
                config=types.GenerateContentConfig(
                    system_instruction="Você é a assistente virtual VetSync. Use a ferramenta 'consultar_disponibilidade' para verificar horários sempre que o tutor perguntar por disponibilidade. Responda em tom amigável.",
                    tools=[consultar_disponibilidade],
                    temperature=0.2,
                )
            )
            chat_response = call_with_retry(chat.send_message, full_prompt + f"Mensagem atual do tutor: {prompt}")
            texto_final_ia = chat_response.text

            # Passo 2: Extrair os dados para o Schema JSON exigido pelo banco de dados
            extracao_prompt = f"Baseado nesta conversa final:\n{full_prompt}\nUsuário: {prompt}\nIA: {texto_final_ia}\n\nExtraia os dados estruturados do agendamento."
            
            extracao_response = call_with_retry(
                self.client.models.generate_content,
                model=self.model_id,
                contents=extracao_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SCHEDULE_SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    response_schema=SchedulingIntent,
                    temperature=0.0,
                )
            )
            
            if not extracao_response.text:
                raise AssistantGatewayError("API returned empty text for scheduling extraction.")
                
            data = json.loads(extracao_response.text)
            
            # Forçar o rascunho a ser a resposta inteligente que o Function Calling gerou
            data["message_draft"] = texto_final_ia
            
            return SchedulingIntent(**data)
            
        except Exception as e:
            raise AssistantGatewayError(f"Erro ao processar intent de agendamento no Gemini: {str(e)}")

    def parse_triage_intent(self, prompt: str, context: dict = None) -> TriageResult:
        try:
            full_prompt = ""
            if context and "history" in context:
                history = context.pop("history")
                history_text = "\n".join([f"{msg['role'].capitalize()}: {msg['text']}" for msg in history])
                full_prompt += f"Histórico de mensagens:\n{history_text}\n\n"
                
            full_prompt += f"Contexto opcional: {json.dumps(context)}\n\n" if context else ""
            full_prompt += f"Mensagem atual do tutor: {prompt}"
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
            full_prompt = ""
            if context and "history" in context:
                history = context.pop("history")
                history_text = "\n".join([f"{msg['role'].capitalize()}: {msg['text']}" for msg in history])
                full_prompt += f"Histórico de mensagens:\n{history_text}\n\n"
                
            full_prompt += f"Contexto opcional: {json.dumps(context)}\n\n" if context else ""
            full_prompt += f"Mensagem atual do tutor: {prompt}"
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

    def orchestrate_intent(self, prompt: str) -> OrchestratorResult:
        try:
            system_instruction = (
                "Você é o orquestrador de intenções do sistema veterinário VetSync. "
                "Classifique a mensagem do usuário em uma das seguintes categorias: "
                "AGENDAMENTO (para marcar, cancelar, alterar consultas), "
                "TRIAGEM (relato de sintomas ou problemas com o pet antes de ir à clínica), "
                "POS_ATENDIMENTO (instruções do médico veterinário para o prontuário), "
                "CHECKIN (relato do tutor sobre a recuperação pós-cirúrgica do pet), "
                "ou OUTRO (se não se encaixar em nenhuma). "
                "Retorne o resultado em JSON."
            )
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=OrchestratorResult,
                    temperature=0.0,
                )
            )
            
            if not response.text:
                raise AssistantGatewayError("API returned empty text for orchestrator.")
                
            data = json.loads(response.text)
            return OrchestratorResult(**data)
            
        except Exception as e:
            raise AssistantGatewayError(f"Erro ao processar orquestração no Gemini: {str(e)}")

    def parse_doctor_command(self, prompt: str) -> dict:
        try:
            from domain.models.models import DoctorCommandIntent
            
            def consultar_historico(tutor_name: str, pet_name: str = None) -> str:
                """Busca no banco de dados o histórico clínico, receitas e prontuários do pet do tutor informado."""
                print(f"-> [Function Calling] IA buscou histórico de: {tutor_name}, pet: {pet_name}")
                return f"Histórico de {tutor_name}: Última consulta há 2 meses. Receita: Dipirona gotas. Prontuário: Animal chegou com dores leves, mas liberado bem."

            system_instruction = (
                "Você é a assistente do médico veterinário (VetSync). O médico pode pedir duas coisas: "
                "1) Puxar o histórico de um paciente (use a ferramenta consultar_historico). "
                "2) Enviar uma mensagem para o tutor, por exemplo, marcando retorno. "
                "Retorne SEMPRE um JSON no schema DoctorCommandIntent. "
                "Se for pedir histórico, extraia os dados com a ferramenta, e coloque o resultado no history_summary. A action deve ser CONSULTAR_HISTORICO. "
                "Se for mandar mensagem para o tutor (ex: 'mande mensagem pra ele marcando retorno em 15 dias'), crie a mensagem amigável no message_draft, e a action deve ser ENVIAR_MENSAGEM."
            )
            
            chat = self.client.chats.create(
                model=self.model_id,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=[consultar_historico],
                    temperature=0.2,
                )
            )
            chat_response = chat.send_message(prompt)
            texto_intermediario = chat_response.text

            # Passo 2: Extrair JSON
            extracao_prompt = f"Usuário: {prompt}\nContexto de ferramenta: {texto_intermediario}\nExtraia os dados estruturados conforme o schema."
            extracao_response = self.client.models.generate_content(
                model=self.model_id,
                contents=extracao_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=DoctorCommandIntent,
                    temperature=0.0,
                )
            )
            
            data = json.loads(extracao_response.text)
            return data
            
        except Exception as e:
            raise AssistantGatewayError(f"Erro ao processar comando do doutor no Gemini: {str(e)}")
