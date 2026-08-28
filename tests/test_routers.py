from fastapi.testclient import TestClient
from main import app
from application.ports import IAssistantGateway, AssistantGatewayError
from presentation.routers import get_gateway
from domain.models.models import ClinicalPostCarePlan, SchedulingIntent

class MockAssistantGateway(IAssistantGateway):
    def __init__(self, fail=False):
        self.fail = fail

    def parse_intent(self, prompt: str) -> ClinicalPostCarePlan:
        if self.fail:
            raise AssistantGatewayError("Erro simulado")
        return ClinicalPostCarePlan(
            pet_name="Bidu",
            tutor_name="Ana",
            days_until_follow_up=15,
            follow_up_reason="Vacina",
            attach_prescription=False,
            attach_medical_record=False,
            message_draft="Olá Ana, o Bidu precisa voltar em 15 dias."
        )

    def parse_scheduling_intent(self, prompt: str) -> SchedulingIntent:
        if self.fail:
            raise AssistantGatewayError("Erro simulado")
        return SchedulingIntent(
            action="CONSULTAR",
            date_reference="hoje",
            time_reference="tarde",
            doctor_name=None,
            patient_name=None,
            state=None,
            message_draft="Quais os horários livres hoje a tarde?"
        )

    def parse_triage_intent(self, prompt: str, context: dict = None):
        from domain.models.models import TriageResult
        if self.fail:
            raise AssistantGatewayError("Erro simulado")
        return TriageResult(
            urgency_level="EMERGENCIA",
            identified_symptoms=["dor"],
            suggested_action="Ação",
            auto_reply_draft="Rascunho",
            notify_team=True
        )

    def parse_checkin_intent(self, prompt: str, context: dict = None):
        from domain.models.models import CheckinResult
        if self.fail:
            raise AssistantGatewayError("Erro simulado")
        return CheckinResult(
            recovery_status="ALERTA_MODERADO",
            red_flags=["febre"],
            notify_veterinarian=True,
            message_draft="Rascunho checkin"
        )

client = TestClient(app)

def override_get_gateway_success():
    return MockAssistantGateway(fail=False)

def override_get_gateway_failure():
    return MockAssistantGateway(fail=True)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_parse_intent_success():
    app.dependency_overrides[get_gateway] = override_get_gateway_success
    
    response = client.post("/api/v1/assistant/parse-intent", json={"prompt": "Bidu tomou vacina hoje, retorno em 15 dias, fala pra Ana."})
    
    assert response.status_code == 200
    data = response.json()
    assert data["pet_name"] == "Bidu"
    assert data["tutor_name"] == "Ana"
    
    app.dependency_overrides.clear()

def test_parse_intent_bad_request():
    app.dependency_overrides[get_gateway] = override_get_gateway_success
    
    response = client.post("/api/v1/assistant/parse-intent", json={"prompt": ""})
    
    assert response.status_code == 400
    
    app.dependency_overrides.clear()

def test_parse_intent_gateway_error():
    app.dependency_overrides[get_gateway] = override_get_gateway_failure
    
    response = client.post("/api/v1/assistant/parse-intent", json={"prompt": "teste"})
    
    assert response.status_code == 400
    assert "Falha na integração" in response.json()["detail"]
    
    app.dependency_overrides.clear()

def test_parse_scheduling_success():
    app.dependency_overrides[get_gateway] = override_get_gateway_success
    
    response = client.post("/api/v1/assistant/parse-scheduling", json={"prompt": "Tem horário hoje a tarde?"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["action"] == "CONSULTAR"
    
    app.dependency_overrides.clear()
