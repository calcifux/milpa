"""Punto de entrada de Celery (paquete). Re-exporta el `celery_app` para que
los consumidores sigan importando con `from app.Core.CeleryApp import celery_app`.
"""

from app.Core.CeleryApp.CeleryApp import celery_app
from app.Core.CeleryApp.Dispatch import QueueUnavailableError, broker_guard

__all__ = ["QueueUnavailableError", "broker_guard", "celery_app"]
