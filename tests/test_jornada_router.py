import pytest
from fastapi import HTTPException

from presentation.routers.jornada_router import PrepararRequest, PosConsultaRequest, preparar, pos_consulta


class FakeJava:
    def list_pets(self, token):
        assert token == "tutor-token"
        return [{"idPet": 7, "nmPet": "Ayla"}]

    def get_event_details(self, token, event_id):
        return {"idEvento": event_id, "idPet": 7}

    def get_record(self, token, pet_id):
        return {
            "orientacoes": [
                {"id": 2, "eventoId": 10, "titulo": "Cuidados", "texto": "Texto do veterinário", "autor": "Dra. Ana"},
                {"id": 3, "eventoId": 11, "titulo": "Outra consulta", "texto": "Não incluir"},
            ],
            "receitas": [
                {"id": 4, "eventoId": 10, "medicamento": "Produto registrado", "posologia": "Texto da receita", "status": "LIBERADO"},
                {"id": 5, "eventoId": 10, "medicamento": "Pendente", "posologia": "Não incluir", "status": "SOLICITADO"},
            ],
        }

    def list_events(self, token):
        return []

    def get_pet_plans(self, token, pet_id):
        return [{"idPlano": 6, "status": "EM_ANDAMENTO", "nmVeterinario": "Dra. Ana", "itens": []}]


class FakeGemini:
    def preparar_consulta(self, relato, nome_pet):
        assert nome_pet == "Ayla"
        return {"resumo": relato, "pontos": [relato], "perguntas": ["Quando retornar?"]}


USER = {"token": "tutor-token", "username": "tutor@example.com"}


def test_preparacao_requer_pet_do_tutor():
    with pytest.raises(HTTPException) as error:
        preparar(PrepararRequest(petId=9, relato="Mudança observada há dois dias"), USER, FakeJava(), FakeGemini())
    assert error.value.status_code == 404


def test_preparacao_retorna_rascunho_identificado():
    result = preparar(PrepararRequest(petId=7, relato="Mudança observada há dois dias"), USER, FakeJava(), FakeGemini())
    assert result["origem"] == "IA_RASCUNHO"
    assert result["perguntas"] == ["Quando retornar?"]


def test_pos_consulta_exclui_receita_nao_liberada_e_outro_evento():
    result = pos_consulta(PosConsultaRequest(petId=7, eventoId=10), USER, FakeJava())
    assert [item["id"] for item in result["orientacoes"]] == [2]
    assert [item["id"] for item in result["medicamentos"]] == [4]
    assert [item["id"] for item in result["planosAtivos"]] == [6]
    assert result["origem"] == "REGISTROS_VETERINARIOS"
