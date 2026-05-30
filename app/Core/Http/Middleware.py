"""Stack base de middlewares del framework (≈ config básica de Laravel / filter
chain de Spring Security): CORS, TrustedHost, GZip — manejados por Settings con
defaults SEGUROS (si no configuras, no expones de más).

EL ORDEN IMPORTA: el último que se agrega es el más EXTERNO (corre primero en el
request). Por eso CORS se agrega al final (outermost), como recomienda FastAPI.
Para middlewares PROPIOS de un módulo, lo idiomático NO es global: declara
`APIRouter(dependencies=[...])` en el controller del módulo (per-route, viaja con
el módulo). El registry global con prioridad se hará on-demand si hace falta.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.Core.Config import settings


def _csv(value: str) -> list[str]:
    """Parte una cadena coma-separada en lista, sin vacíos."""
    return [item.strip() for item in value.split(",") if item.strip()]


def register_middlewares(app: FastAPI) -> None:
    """Agrega el stack base según Settings. Se agregan de ADENTRO hacia AFUERA:
    GZip (interno) → TrustedHost → CORS (externo). Cada uno solo si aplica."""
    # GZip: el más interno (comprime la respuesta ya formada).
    if settings.gzip_enabled:
        app.add_middleware(GZipMiddleware, minimum_size=settings.gzip_min_size)

    # TrustedHost: rechaza Host headers no permitidos. "*" = off.
    trusted = _csv(settings.trusted_hosts) or ["*"]
    if trusted != ["*"]:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted)

    # CORS: el más EXTERNO (se agrega al final). Solo si hay orígenes configurados.
    origins = _csv(settings.cors_allow_origins)
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_methods=_csv(settings.cors_allow_methods) or ["*"],
            allow_headers=_csv(settings.cors_allow_headers) or ["*"],
            allow_credentials=settings.cors_allow_credentials,
        )
