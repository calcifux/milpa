"""Handlers de excepción GLOBALES: normalizan los errores a un sobre JSON único.

Sin esto, cada excepción no controlada se va como un 500 técnico (body inconsistente,
a veces con internals), y cada error de negocio se traduce a mano a `HTTPException` en
cada controller, con formatos distintos. Aquí se instalan dos handlers:

  - `DomainError` (y subclases): respuesta de NEGOCIO normalizada — su `status_code` y el
    cuerpo `{error_code, message, details}`. Es un error esperado: se loguea a INFO.
  - catch-all `Exception`: cualquier cosa NO prevista (bug, infra caída) → 500 genérico +
    log con traceback COMPLETO, SIN filtrar el mensaje real de la excepción al cliente.

Es ADITIVO: NO toca los `HTTPException` de FastAPI (auth/validación/infra siguen con su
`{"detail": ...}`), ni el 422 de validación de Pydantic.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from loguru import logger

from app.Core.Errors import DomainError


def register_exception_handlers(app: FastAPI) -> None:
    """Instala los handlers globales en la app (lo llama `create_app`)."""

    async def _handle_domain_error(_request: Request, exc: Exception) -> JSONResponse:
        # exc: Exception (firma que pide Starlette); narrow para el type-checker + seguridad.
        assert isinstance(exc, DomainError)
        # Error de NEGOCIO: esperado, no es un bug. INFO con su código estable.
        logger.info("DomainError | {code} | {msg}", code=exc.error_code, msg=exc.message)
        return JSONResponse(status_code=exc.status_code, content=exc.to_payload())

    async def _handle_unexpected_error(_request: Request, exc: Exception) -> JSONResponse:
        # No previsto: ES un bug o infra caída. Traceback COMPLETO al log; al cliente, un
        # 500 genérico SIN internals (nunca exponemos el mensaje real de la excepción).
        logger.exception("Unhandled exception | {t}", t=type(exc).__name__)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error_code": "internal_error", "message": "Error interno del servidor", "details": None},
        )

    app.add_exception_handler(DomainError, _handle_domain_error)
    app.add_exception_handler(Exception, _handle_unexpected_error)
