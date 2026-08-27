from abc import ABC, abstractmethod
from domain.models import ClinicalPostCarePlan, SchedulingIntent, TriageResult, CheckinResult, OrchestratorResult

class AssistantGatewayError(Exception):
    """Exceção base para erros de integração com a IA."""
    pass

class IAssistantGateway(ABC):
    @abstractmethod
    def parse_intent(self, prompt: str) -> ClinicalPostCarePlan:
        pass

    @abstractmethod
    def parse_scheduling_intent(self, prompt: str, context: dict = None) -> SchedulingIntent:
        pass
        
    @abstractmethod
    def parse_triage_intent(self, prompt: str, context: dict = None) -> TriageResult:
        pass
        
    @abstractmethod
    def parse_checkin_intent(self, prompt: str, context: dict = None) -> CheckinResult:
        pass

    @abstractmethod
    def orchestrate_intent(self, prompt: str) -> 'OrchestratorResult':
        pass
