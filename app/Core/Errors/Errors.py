"""Errores de DOMINIO, neutrales a la capa de transporte (sin FastAPI).

Los lanza el dominio (services, repositories) para expresar lo que SABE explicar:
"no existe", "ya existe / choca con el estado", "no autorizado para esto". Cada uno
lleva:
  - `error_code`: código ESTABLE y legible por máquina (los clientes ramifican en él),
  - `message`: texto legible por humanos,
  - `details`: datos opcionales (qué id, qué campo, etc.),
  - `status_code`: el HTTP al que mapea.

El controller NO las atrapa: el handler global (`app/Core/Http/ExceptionHandler.py`) las
convierte en un sobre JSON único. Viven FUERA de `Http` a propósito, para que la capa de
persistencia (p. ej. `Repository.find_or_fail`) pueda lanzarlas sin importar el framework
web (mantiene el layering: la persistencia no depende de FastAPI).
"""

from __future__ import annotations

from typing import Any


class DomainError(Exception):
    """Base de los errores de negocio. Subclasea para fijar `status_code`/`error_code`
    por defecto, o instánciala directo para un caso puntual:

        raise DomainError("Saldo insuficiente", error_code="insufficient_funds", status_code=409)
    """

    status_code: int = 400
    error_code: str = "domain_error"

    def __init__(
        self,
        message: str,
        *,
        details: Any = None,
        error_code: str | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details
        # Permiten override por-instancia sin tener que subclasear para cada caso.
        if error_code is not None:
            self.error_code = error_code
        if status_code is not None:
            self.status_code = status_code

    def to_payload(self) -> dict[str, Any]:
        """El sobre JSON estándar que verá el cliente (`error_code`/`message`/`details`)."""
        return {"error_code": self.error_code, "message": self.message, "details": self.details}


class ResourceNotFoundError(DomainError):
    """El recurso pedido no existe (= 404). Lo usa, p. ej., `Repository.find_or_fail()`."""

    status_code = 404
    error_code = "resource_not_found"


class ConflictError(DomainError):
    """Choque con el estado actual: duplicado, transición inválida, etc. (= 409)."""

    status_code = 409
    error_code = "conflict"


class UnauthorizedError(DomainError):
    """Falta autenticación / credencial inválida (= 401)."""

    status_code = 401
    error_code = "unauthorized"


class ForbiddenError(DomainError):
    """Autenticado pero sin permiso para esta acción (= 403)."""

    status_code = 403
    error_code = "forbidden"
