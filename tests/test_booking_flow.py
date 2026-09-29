from datetime import datetime, timedelta

import pytest

from application.booking_flow import BOOKING_TIMEZONE, BookingFlowError, BookingFlowService, BookingSessionStore
from infrastructure.java_vetsync_client import JavaVetSyncConflictError, JavaVetSyncError
from presentation.routers.orquestrador_router import is_scheduling_turn


class FakeJavaAgenda:
    def __init__(self, *, slots=None, availability_error=False, conflict=False):
        self.slots = slots if slots is not None else [
            {
                "idTipoEvento": 8,
                "nmTipoEvento": "Consulta de rotina",
                "idVeterinario": 4,
                "nmVeterinario": "Dra. Ana",
                "hrEvento": "12:00",
            }
        ]
        self.availability_error = availability_error
        self.conflict = conflict
        self.created_payload = None

    def available_slots(self, token, selected_date, modality):
        assert token == "token-do-tutor"
        assert modality == "CLINICO_GERAL"
        if self.availability_error:
            raise JavaVetSyncError("agenda indisponível")
        return {"data": selected_date, "slots": self.slots}

    def list_pets(self, token):
        assert token == "token-do-tutor"
        return [
            {"idPet": 2, "nmPet": "Ayla", "nmEspecie": "Cachorro"},
            {"idPet": 9, "nmPet": "Morgana", "nmEspecie": "Cachorro"},
        ]

    def create_event(self, token, payload):
        assert token == "token-do-tutor"
        self.created_payload = payload
        if self.conflict:
            raise JavaVetSyncConflictError("slot ocupado")
        return {
            "dtEvento": payload["dtEvento"],
            "hrEvento": payload["hrEvento"],
            "nmTipoEvento": "Consulta de rotina",
            "nmVeterinario": "Dra. Ana",
        }


def option_id(block, label):
    return next(option["id"] for option in block["opcoes"] if option["rotulo"] == label)


def test_checkup_tomorrow_follows_slots_pet_confirmation_and_creation():
    java = FakeJavaAgenda()
    flow = BookingFlowService(java, BookingSessionStore())
    expected_date = (datetime.now(BOOKING_TIMEZONE).date() + timedelta(days=1)).isoformat()

    slots = flow.start("Quero marcar um check-up amanhã", "felipe", "token-do-tutor")
    assert slots.block["tipo"] == "SELECIONAR_HORARIO"

    pets = flow.select(slots.block["sessaoId"], option_id(slots.block, "12:00"), "felipe", "token-do-tutor")
    assert pets.block["tipo"] == "SELECIONAR_PET"
    assert {option["rotulo"] for option in pets.block["opcoes"]} == {"Ayla", "Morgana"}

    confirmation = flow.select(pets.block["sessaoId"], option_id(pets.block, "Ayla"), "felipe", "token-do-tutor")
    assert confirmation.block["tipo"] == "CONFIRMAR_RESERVA"

    completed = flow.select(
        confirmation.block["sessaoId"], option_id(confirmation.block, "Confirmar reserva"), "felipe", "token-do-tutor"
    )
    assert completed.block is None
    assert "Consulta confirmada para Ayla" in completed.message
    assert java.created_payload == {
        "idPet": 2,
        "idTipoEvento": 8,
        "idVeterinario": 4,
        "dtEvento": expected_date,
        "hrEvento": "12:00",
        "dsObservacao": None,
    }


def test_checkup_is_recognized_as_a_scheduling_turn():
    assert is_scheduling_turn("Quero marcar um check-up amanhã", {})


def test_health_guidance_is_preserved_when_availability_fails():
    flow = BookingFlowService(FakeJavaAgenda(availability_error=True), BookingSessionStore())

    with pytest.raises(BookingFlowError, match="avaliação presencial") as error:
        flow.start("Ayla acordou xoxa, quero uma consulta amanhã", "felipe", "token-do-tutor")

    assert "Não consegui consultar os horários" in str(error.value)


def test_conflict_returns_current_slots_without_creating_a_second_event():
    java = FakeJavaAgenda(conflict=True)
    flow = BookingFlowService(java, BookingSessionStore())
    slots = flow.start("Quero marcar uma consulta amanhã", "felipe", "token-do-tutor")
    pets = flow.select(slots.block["sessaoId"], option_id(slots.block, "12:00"), "felipe", "token-do-tutor")
    confirmation = flow.select(pets.block["sessaoId"], option_id(pets.block, "Ayla"), "felipe", "token-do-tutor")

    replacement = flow.select(
        confirmation.block["sessaoId"], option_id(confirmation.block, "Confirmar reserva"), "felipe", "token-do-tutor"
    )

    assert replacement.block["tipo"] == "SELECIONAR_HORARIO"
    assert replacement.message.startswith("Esse horário acabou de ficar indisponível.")
