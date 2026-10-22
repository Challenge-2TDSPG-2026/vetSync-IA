"""Cliente do contrato público do backend Java usado pela SIA.

O Bearer recebido pelo FastAPI é repassado ao Java. Assim, a regra de posse do
pet continua sendo aplicada pelo serviço que cria o evento.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx


class JavaVetSyncError(Exception):
    pass


class JavaVetSyncConflictError(JavaVetSyncError):
    pass


class JavaVetSyncAccessError(JavaVetSyncError):
    pass


@dataclass
class JavaVetSyncClient:
    base_url: str | None = None
    timeout: float = 10.0

    def __post_init__(self) -> None:
        self.base_url = (self.base_url or os.getenv("JAVA_API_BASE_URL") or "").rstrip("/")

    def scheduling_context(self, bearer_token: str) -> dict[str, list[dict[str, Any]]]:
        """Busca somente os catálogos reais necessários para a escolha do tutor."""
        return {
            "pets": self._get("/pets", bearer_token),
            "tipos_evento": self._get("/tipos-evento", bearer_token),
            "veterinarios": self._get("/veterinarios", bearer_token),
        }

    def create_event(self, bearer_token: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/eventos", bearer_token, json=payload)

    def available_slots(self, bearer_token: str, data: str, modalidade: str = "CLINICO_GERAL") -> dict[str, Any]:
        """Consulta slots calculados pelo Java sem criar uma reserva."""
        return self._request(
            "GET",
            "/agenda/slots",
            bearer_token,
            params={"data": data, "modalidade": modalidade},
        )

    def list_pets(self, bearer_token: str) -> list[dict[str, Any]]:
        """Lista apenas os pets autorizados para o tutor autenticado."""
        result = self._get("/pets", bearer_token)
        if not isinstance(result, list):
            raise JavaVetSyncError("A API Java devolveu uma lista de pets inválida.")
        return result

    def list_events(self, bearer_token: str) -> list[dict[str, Any]]:
        """Lista os eventos visíveis ao tutor para contextualizar o acompanhamento."""
        result = self._get("/eventos", bearer_token)
        if not isinstance(result, list):
            raise JavaVetSyncError("A API Java devolveu uma lista de eventos inválida.")
        return result

    def get_pet(self, bearer_token: str, pet_id: int) -> dict[str, Any]:
        return self._get(f"/pets/{pet_id}", bearer_token)

    def get_event_details(self, bearer_token: str, event_id: int) -> dict[str, Any]:
        return self._get(f"/eventos/{event_id}/detalhes", bearer_token)

    def get_event_guidance(self, bearer_token: str, event_id: int) -> list[dict[str, Any]]:
        result = self._get(f"/eventos/{event_id}/orientacoes", bearer_token)
        if not isinstance(result, list):
            raise JavaVetSyncError("A API Java devolveu orientações inválidas.")
        return result

    def get_record(self, bearer_token: str, pet_id: int) -> dict[str, Any]:
        return self._get(f"/pets/{pet_id}/prontuario?secoes=ORIENTACOES,RECEITAS", bearer_token)

    def get_pet_plans(self, bearer_token: str, pet_id: int) -> list[dict[str, Any]]:
        result = self._get(f"/planos/pet/{pet_id}", bearer_token)
        if not isinstance(result, list):
            raise JavaVetSyncError("A API Java devolveu planos inválidos.")
        return result

    def save_booking_session(self, bearer_token: str, session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("PUT", f"/sia/agendamentos/sessoes/{session_id}", bearer_token, json=payload)

    def get_booking_session(self, bearer_token: str, session_id: str) -> dict[str, Any]:
        return self._get(f"/sia/agendamentos/sessoes/{session_id}", bearer_token)

    def _get(self, path: str, bearer_token: str) -> Any:
        return self._request("GET", path, bearer_token)

    def _request(self, method: str, path: str, bearer_token: str, **kwargs: Any) -> Any:
        if not self.base_url:
            raise JavaVetSyncError("JAVA_API_BASE_URL não está configurada.")
        if not bearer_token or bearer_token == "mock_token_dev":
            raise JavaVetSyncError("Não há um token de tutor válido para consultar a API Java.")

        try:
            response = httpx.request(
                method,
                f"{self.base_url}{path}",
                headers={"Authorization": f"Bearer {bearer_token}"},
                timeout=self.timeout,
                **kwargs,
            )
        except httpx.HTTPError as exc:
            raise JavaVetSyncError("Não foi possível comunicar com a agenda da clínica.") from exc

        if response.status_code == 409:
            raise JavaVetSyncConflictError("O horário acabou de ser ocupado ou está bloqueado.")
        if response.status_code in (401, 403):
            raise JavaVetSyncAccessError("Acesso não autorizado pelo backend Java.")
        if response.is_error:
            raise JavaVetSyncError("A agenda da clínica não pôde concluir esta solicitação agora.")

        try:
            return response.json()
        except ValueError as exc:
            raise JavaVetSyncError("A API Java devolveu uma resposta inválida.") from exc
