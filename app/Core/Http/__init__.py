"""Kernel web del framework. Re-exporta la app factory `create_app` para que
los entrypoints (p. ej. `jornal serve`) la levanten con
`uvicorn.run("app.Core.Http.Http:create_app", factory=True)`.
"""

from app.Core.Http.Http import create_app
from app.Core.Http.Routing import Controller, Delete, Get, Patch, Post, Put

__all__ = ["Controller", "Delete", "Get", "Patch", "Post", "Put", "create_app"]
