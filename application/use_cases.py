from domain.models import ClinicalPostCarePlan, SchedulingIntent
from application.ports import IAssistantGateway, AssistantGatewayError

class ProcessPostCareIntentUseCaseError(Exception):
    pass

class ProcessPostCareIntentUseCase:
    def __init__(self, gateway: IAssistantGateway):
        self.gateway = gateway
        
    def execute(self, prompt: str) -> ClinicalPostCarePlan:
        if not prompt or not prompt.strip():
            raise ProcessPostCareIntentUseCaseError("O prompt não pode estar vazio.")
            
        try:
            return self.gateway.parse_intent(prompt)
        except AssistantGatewayError as e:
            raise ProcessPostCareIntentUseCaseError(f"Falha na integração: {str(e)}")
        except Exception as e:
            raise ProcessPostCareIntentUseCaseError(f"Erro inesperado: {str(e)}")

class ProcessSchedulingIntentUseCaseError(Exception):
    pass

class ProcessSchedulingIntentUseCase:
    def __init__(self, gateway: IAssistantGateway):
        self.gateway = gateway
        
    def execute(self, prompt: str) -> SchedulingIntent:
        if not prompt or not prompt.strip():
            raise ProcessSchedulingIntentUseCaseError("O prompt não pode estar vazio.")
            
        try:
            return self.gateway.parse_scheduling_intent(prompt)
        except AssistantGatewayError as e:
            raise ProcessSchedulingIntentUseCaseError(f"Falha na integração: {str(e)}")
        except Exception as e:
            raise ProcessSchedulingIntentUseCaseError(f"Erro inesperado: {str(e)}")
