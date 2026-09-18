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
        if response.is_error:
            raise JavaVetSyncError("A agenda da clínica não pôde concluir esta solicitação agora.")

        try:
            return response.json()
        except ValueError as exc:
            raise JavaVetSyncError("A API Java devolveu uma resposta inválida.") from exc
