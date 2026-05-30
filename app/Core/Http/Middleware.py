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
from app.Core.Http.SecurityHeaders import SecurityHeadersMiddleware


def _csv(value: str) -> list[str]:
    """Parte una cadena coma-separada en lista, sin vacíos."""
    return [item.strip() for item in value.split(",") if item.strip()]


def _security_headers() -> dict[str, str]:
    """Arma el set de security headers a inyectar, según Settings (defaults seguros)."""
    headers = {
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": settings.security_referrer_policy,
    }
    if settings.security_frame_options:
        headers["X-Frame-Options"] = settings.security_frame_options
    if settings.content_security_policy:
        headers["Content-Security-Policy"] = settings.content_security_policy
    if settings.hsts_enabled:
        value = f"max-age={settings.hsts_max_age}"
        if settings.hsts_include_subdomains:
            value += "; includeSubDomains"
        headers["Strict-Transport-Security"] = value
    return headers


def register_middlewares(app: FastAPI) -> None:
    """Agrega el stack base según Settings. Se agregan de ADENTRO hacia AFUERA:
    SecurityHeaders (interno) → GZip → TrustedHost → CORS (externo). Cada uno solo si aplica."""
    # SecurityHeaders: el más interno (ve la respuesta ya formada y le pega los headers).
    if settings.security_headers_enabled:
        app.add_middleware(SecurityHeadersMiddleware, headers=_security_headers())

    # GZip: comprime la respuesta ya formada.
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
