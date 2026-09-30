from application.recovery_flow import RecoveryFlowService, RecoveryResponse, RecoverySessionStore
from presentation.routers.orquestrador_router import MensagemChatRequest, processar_chat_universal


def test_refusing_the_recovery_report_ends_the_pending_question():
    sessions = RecoverySessionStore()
    session = sessions.create("felipe")
    session.state = "AGUARDANDO_RELATO"
    session.selected["nmPet"] = "Morgana"
    flow = RecoveryFlowService(object(), sessions)

    response = flow.respond_to_report("felipe", "Não quero mais informar como ela está")

    assert response is not None
    assert "Não preciso dessa informação" in response.message
    assert sessions.active_for("felipe") is None


class PendingRecoveryFlow:
    def __init__(self):
        self.finished_for = []

    def finish_pending_report(self, tutor_id):
        self.finished_for.append(tutor_id)

    def respond_to_report(self, tutor_id, report):
        raise AssertionError("Um pedido explícito de consulta não deve responder ao acompanhamento")


class BookingFlowSpy:
    def __init__(self):
        self.calls = []

    def start(self, message, tutor_id, token):
        self.calls.append((message, tutor_id, token))
        return RecoveryResponse("Escolha um horário disponível.")


def test_explicit_scheduling_request_has_priority_over_pending_recovery():
    recovery_flow = PendingRecoveryFlow()
    booking_flow = BookingFlowSpy()

    response = processar_chat_universal(
        MensagemChatRequest(message="Quero marcar uma consulta"),
        usuario_logado={"username": "felipe", "token": "token-do-tutor"},
        gateway=None,
        booking_flow=booking_flow,
        recovery_flow=recovery_flow,
    )

    assert response == {"mensagem": "Escolha um horário disponível."}
    assert recovery_flow.finished_for == ["felipe"]
    assert booking_flow.calls == [("Quero marcar uma consulta", "felipe", "token-do-tutor")]
