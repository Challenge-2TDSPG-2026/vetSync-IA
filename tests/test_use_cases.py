import pytest
from application.use_cases import ProcessPostCareIntentUseCase, ProcessSchedulingIntentUseCase, ProcessPostCareIntentUseCaseError, ProcessSchedulingIntentUseCaseError
from application.ports import IAssistantGateway, AssistantGatewayError
from domain.models.models import ClinicalPostCarePlan, SchedulingIntent

class MockAssistantGateway(IAssistantGateway):
    def __init__(self):
        self.should_fail = False

    def parse_intent(self, prompt: str) -> ClinicalPostCarePlan:
        if self.should_fail:
            raise AssistantGatewayError("Mocked failure")
        return ClinicalPostCarePlan(
            pet_name="Rex",
            tutor_name="João",
            days_until_follow_up=7,
            follow_up_reason="Retirada de pontos",
            attach_prescription=False,
            attach_medical_record=False,
            message_draft="Olá João, o Rex precisa voltar em 7 dias."
        )

    def parse_scheduling_intent(self, prompt: str) -> SchedulingIntent:
        if self.should_fail:
            raise AssistantGatewayError("Mocked failure")
        return SchedulingIntent(
            action="RESERVAR",
            date_reference="amanhã",
            time_reference="14:00",
            doctor_name="Dra. Silva",
            patient_name="Rex",
            state="PENDENTE_DOUTOR",
            message_draft="Agendamento solicitado para amanhã às 14:00 com a Dra. Silva."
        )

    def parse_triage_intent(self, prompt: str, context: dict = None):
        from domain.models.models import TriageResult
        if self.should_fail:
            raise AssistantGatewayError("Mocked failure")
        return TriageResult(
            urgency_level="EMERGENCIA",
            identified_symptoms=["dor"],
            suggested_action="Ação",
            auto_reply_draft="Rascunho",
            notify_team=True
        )

    def parse_checkin_intent(self, prompt: str, context: dict = None):
        from domain.models.models import CheckinResult
        if self.should_fail:
            raise AssistantGatewayError("Mocked failure")
        return CheckinResult(
            recovery_status="ALERTA_MODERADO",
            red_flags=["febre"],
            notify_veterinarian=True,
            message_draft="Rascunho checkin"
        )

@pytest.fixture
def mock_gateway():
    return MockAssistantGateway()

def test_process_post_care_intent_success(mock_gateway):
    use_case = ProcessPostCareIntentUseCase(gateway=mock_gateway)
    result = use_case.execute("O Rex operou hoje, o João tem que trazer ele daqui a 7 dias para tirar os pontos")
    
    assert result.pet_name == "Rex"
    assert result.tutor_name == "João"
    assert result.days_until_follow_up == 7

def test_process_post_care_intent_empty_prompt(mock_gateway):
    use_case = ProcessPostCareIntentUseCase(gateway=mock_gateway)
    with pytest.raises(ProcessPostCareIntentUseCaseError):
        use_case.execute("   ")

def test_process_post_care_intent_gateway_error(mock_gateway):
    mock_gateway.should_fail = True
    use_case = ProcessPostCareIntentUseCase(gateway=mock_gateway)
    with pytest.raises(ProcessPostCareIntentUseCaseError, match="Falha na integração: Mocked failure"):
        use_case.execute("O Rex operou hoje")

def test_process_scheduling_intent_success(mock_gateway):
    use_case = ProcessSchedulingIntentUseCase(gateway=mock_gateway)
    result = use_case.execute("Marcar para o Rex amanhã as 14h com a Dra. Silva")
    
    assert result.action == "RESERVAR"
    assert result.date_reference == "amanhã"
    assert result.time_reference == "14:00"

def test_process_scheduling_intent_empty_prompt(mock_gateway):
    use_case = ProcessSchedulingIntentUseCase(gateway=mock_gateway)
    with pytest.raises(ProcessSchedulingIntentUseCaseError):
        use_case.execute("")

def test_process_scheduling_intent_gateway_error(mock_gateway):
    mock_gateway.should_fail = True
    use_case = ProcessSchedulingIntentUseCase(gateway=mock_gateway)
    with pytest.raises(ProcessSchedulingIntentUseCaseError, match="Falha na integração: Mocked failure"):
        use_case.execute("Agendar")
