"""Errores de dominio del framework (neutrales al transporte). Impórtalos desde aquí:

from app.Core.Errors import DomainError, ResourceNotFoundError
"""

from app.Core.Errors.Errors import (
    ConflictError,
    DomainError,
    ForbiddenError,
    ResourceNotFoundError,
    UnauthorizedError,
)

__all__ = [
    "ConflictError",
    "DomainError",
    "ForbiddenError",
    "ResourceNotFoundError",
    "UnauthorizedError",
]
