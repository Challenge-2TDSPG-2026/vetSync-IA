from domain.models import ClinicalPostCarePlan, SchedulingIntent, TriageResult, CheckinResult, OrchestratorResult
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

class ProcessTriageIntentUseCaseError(Exception):
    pass

class ProcessTriageIntentUseCase:
    def __init__(self, gateway: IAssistantGateway):
        self.gateway = gateway
        
    def execute(self, prompt: str, context: dict = None) -> TriageResult:
        if not prompt or not prompt.strip():
            raise ProcessTriageIntentUseCaseError("A mensagem não pode estar vazia.")
            
        try:
            return self.gateway.parse_triage_intent(prompt, context)
        except AssistantGatewayError as e:
            raise ProcessTriageIntentUseCaseError(f"Falha na integração: {str(e)}")
        except Exception as e:
            raise ProcessTriageIntentUseCaseError(f"Erro inesperado: {str(e)}")

class ProcessCheckinIntentUseCaseError(Exception):
    pass

class ProcessCheckinIntentUseCase:
    def __init__(self, gateway: IAssistantGateway):
        self.gateway = gateway
        
    def execute(self, prompt: str, context: dict = None) -> CheckinResult:
        if not prompt or not prompt.strip():
            raise ProcessCheckinIntentUseCaseError("A mensagem não pode estar vazia.")
            
        try:
            return self.gateway.parse_checkin_intent(prompt, context)
        except AssistantGatewayError as e:
            raise ProcessCheckinIntentUseCaseError(f"Falha na integração: {str(e)}")
        except Exception as e:
            raise ProcessCheckinIntentUseCaseError(f"Erro inesperado: {str(e)}")

class ProcessOrchestratorIntentUseCaseError(Exception):
    pass

class ProcessOrchestratorIntentUseCase:
    def __init__(self, gateway: IAssistantGateway):
        self.gateway = gateway
        
    def execute(self, prompt: str) -> 'OrchestratorResult':
        if not prompt or not prompt.strip():
            raise ProcessOrchestratorIntentUseCaseError("A mensagem não pode estar vazia.")
            
        try:
            return self.gateway.orchestrate_intent(prompt)
        except AssistantGatewayError as e:
            raise ProcessOrchestratorIntentUseCaseError(f"Falha na integração: {str(e)}")
        except Exception as e:
            raise ProcessOrchestratorIntentUseCaseError(f"Erro inesperado: {str(e)}")
