"""Tests de los handlers globales de excepción.

Sin BD ni red: se levanta la app factory y se le agregan rutas de prueba que lanzan
cada tipo de error. `raise_server_exceptions=False` deja que el handler 500 FORME la
respuesta en vez de re-lanzar la excepción dentro del test.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.Core.Errors import ConflictError, DomainError, ResourceNotFoundError
from app.Core.Http.Http import create_app


def _client() -> TestClient:
    app = create_app()

    @app.get("/_test/not-found")
    def _not_found() -> dict[str, str]:
        raise ResourceNotFoundError("La compañía 7 no existe", details={"id": 7})

    @app.get("/_test/conflict")
    def _conflict() -> dict[str, str]:
        raise ConflictError("Ya existe un registro con ese folio")

    @app.get("/_test/custom")
    def _custom() -> dict[str, str]:
        raise DomainError("Saldo insuficiente", error_code="insufficient_funds", status_code=402)

    @app.get("/_test/boom")
    def _boom() -> dict[str, str]:
        raise ValueError("detalle interno secreto que NO debe filtrarse")

    return TestClient(app, raise_server_exceptions=False)


def test_domain_error_maps_to_envelope_and_status() -> None:
    response = _client().get("/_test/not-found")
    assert response.status_code == 404
    assert response.json() == {
        "error_code": "resource_not_found",
        "message": "La compañía 7 no existe",
        "details": {"id": 7},
    }


def test_domain_error_subclass_uses_its_status() -> None:
    response = _client().get("/_test/conflict")
    assert response.status_code == 409
    assert response.json()["error_code"] == "conflict"


def test_domain_error_per_instance_overrides() -> None:
    response = _client().get("/_test/custom")
    assert response.status_code == 402
    body = response.json()
    assert body["error_code"] == "insufficient_funds"
    assert body["message"] == "Saldo insuficiente"
    assert body["details"] is None


def test_unexpected_error_returns_generic_500_without_internals() -> None:
    response = _client().get("/_test/boom")
    assert response.status_code == 500
    assert response.json() == {
        "error_code": "internal_error",
        "message": "Error interno del servidor",
        "details": None,
    }
    # El mensaje real de la excepción NUNCA debe filtrarse al cliente.
    assert "secreto" not in response.text


def test_existing_http_exception_is_untouched() -> None:
    # Regresión: el 401 de require_api_key (HTTPException) conserva su {"detail": ...}.
    response = _client().get("/example/secured/ping")
    assert response.status_code == 401
    assert response.json() == {"detail": "API key inválida"}
