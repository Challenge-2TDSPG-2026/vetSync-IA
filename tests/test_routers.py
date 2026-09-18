from fastapi.testclient import TestClient
from main import app
from application.ports import IAssistantGateway, AssistantGatewayError
from presentation.assistant_routers import get_gateway
from presentation.routers.orquestrador_router import get_gemini_gateway, get_java_vetsync_client
from infrastructure.auth.security import verificar_token_externo
from domain.models.models import ClinicalPostCarePlan, SchedulingConversationDecision, SchedulingIntent, OrchestratorResult

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

    def parse_scheduling_intent(self, prompt: str, context: dict = None) -> SchedulingIntent:
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

    def orchestrate_intent(self, prompt: str) -> OrchestratorResult:
        if self.fail:
            raise AssistantGatewayError("Erro simulado")
        return OrchestratorResult(
            intent_category="POS_ATENDIMENTO",
            reasoning="Identificada intenção de pós atendimento"
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


class MockTutorConversationGateway:
    def __init__(self):
        self.calls = []

    def responder_ao_tutor(self, prompt: str, context: dict | None = None) -> str:
        self.calls.append((prompt, context))
        return "Claro! Para amanhã, 09:00 continua disponível para a Morgana."


def test_tutor_chat_preserves_history_and_returns_only_a_message():
    gateway = MockTutorConversationGateway()
    app.dependency_overrides[get_gemini_gateway] = lambda: gateway
    app.dependency_overrides[verificar_token_externo] = lambda: {"username": "luiz"}

    history = [
        {"role": "user", "text": "Quero marcar uma consulta para amanhã."},
        {"role": "assistant", "text": "Tenho 09:00 e 11:00 disponíveis amanhã."},
        {"role": "user", "text": "As 09h"},
    ]
    response = client.post(
        "/api/v1/ia/orquestrador/processar",
        json={"message": "As 09h", "contexto": {"history": history, "pet_ativo": {"nome": "Morgana"}}},
    )

    assert response.status_code == 200
    assert response.json() == {"mensagem": "Claro! Para amanhã, 09:00 continua disponível para a Morgana."}
    assert gateway.calls == [("As 09h", {"history": history, "pet_ativo": {"nome": "Morgana"}, "tutor_id": "luiz"})]
    app.dependency_overrides.clear()


class MockSchedulingConversationGateway:
    def __init__(self):
        self.calls = []

    def decidir_agendamento_tutor(self, prompt, context, catalogos):
        self.calls.append((prompt, context, catalogos))
        return SchedulingConversationDecision(
            message="Vou confirmar a reserva.",
            create_event=True,
            id_pet=2,
            id_tipo_evento=8,
            id_veterinario=4,
            dt_evento="2026-09-20",
            hr_evento="16:00",
            ds_observacao=None,
        )


class FakeJavaAgenda:
    def __init__(self):
        self.payload = None

    def scheduling_context(self, token):
        assert token == "token-real-do-tutor"
        return {
            "pets": [{"idPet": 2, "nmPet": "Ayla"}, {"idPet": 9, "nmPet": "Morgana"}],
            "tipos_evento": [{"idTipoEvento": 8, "nmTipoEvento": "Consulta"}],
            "veterinarios": [{"idVeterinario": 4, "nmVeterinario": "Dra. Ana"}],
        }

    def create_event(self, token, payload):
        assert token == "token-real-do-tutor"
        self.payload = payload
        return {
            "idEvento": 123,
            "idPet": 2,
            "nmTipoEvento": "Consulta",
            "nmVeterinario": "Dra. Ana",
            "dtEvento": "2026-09-20",
            "hrEvento": "16:00",
        }


def test_tutor_chat_creates_event_only_from_real_catalog_choices():
    gateway = MockSchedulingConversationGateway()
    java = FakeJavaAgenda()
    app.dependency_overrides[get_gemini_gateway] = lambda: gateway
    app.dependency_overrides[get_java_vetsync_client] = lambda: java
    app.dependency_overrides[verificar_token_externo] = lambda: {
        "username": "luiz@teste.com",
        "token": "token-real-do-tutor",
    }

    response = client.post(
        "/api/v1/ia/orquestrador/processar",
        json={
            "message": "Pode marcar dia 20 às 16h.",
            "contexto": {"pet_ativo": {"idPet": 9, "nome": "Morgana"}},
        },
    )

    assert response.status_code == 200
    assert response.json() == {"mensagem": "Consulta confirmada para Ayla: Consulta em 20/09/2026, às 16:00, com Dra. Ana."}
    assert java.payload == {
        "idPet": 2,
        "idTipoEvento": 8,
        "idVeterinario": 4,
        "dtEvento": "2026-09-20",
        "hrEvento": "16:00",
        "dsObservacao": None,
    }
    assert gateway.calls[0][1]["pet_ativo"] == {"idPet": 9, "nome": "Morgana"}
    app.dependency_overrides.clear()
