from domain.models import ClinicalPostCarePlan, SchedulingIntent
from infrastructure.gemini_gateway import GeminiGateway, GeminiGatewayError

class ProcessPostCareIntentUseCaseError(Exception):
    pass

class ProcessPostCareIntentUseCase:
    def __init__(self, gemini_gateway: GeminiGateway = None):
        # Injeção de dependência simplificada para o Gateway
        self.gateway = gemini_gateway or GeminiGateway()
        
    def execute(self, prompt: str) -> ClinicalPostCarePlan:
        if not prompt or not prompt.strip():
            raise ProcessPostCareIntentUseCaseError("O prompt não pode estar vazio.")
            
        try:
            return self.gateway.parse_intent(prompt)
        except GeminiGatewayError as e:
            raise ProcessPostCareIntentUseCaseError(f"Falha na integração: {str(e)}")
        except Exception as e:
            raise ProcessPostCareIntentUseCaseError(f"Erro inesperado: {str(e)}")

class ProcessSchedulingIntentUseCaseError(Exception):
    pass

class ProcessSchedulingIntentUseCase:
    def __init__(self, gemini_gateway: GeminiGateway = None):
        self.gateway = gemini_gateway or GeminiGateway()
        
    def execute(self, prompt: str) -> SchedulingIntent:
        if not prompt or not prompt.strip():
            raise ProcessSchedulingIntentUseCaseError("O prompt não pode estar vazio.")
            
        try:
            return self.gateway.parse_scheduling_intent(prompt)
        except GeminiGatewayError as e:
            raise ProcessSchedulingIntentUseCaseError(f"Falha na integração: {str(e)}")
        except Exception as e:
            raise ProcessSchedulingIntentUseCaseError(f"Erro inesperado: {str(e)}")
