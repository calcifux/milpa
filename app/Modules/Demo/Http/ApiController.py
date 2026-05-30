"""Carril API (JWT) del demo — para frontends SEPARADOS (SPA/móvil).

`POST /api/login` → JWT; el resto exige `Authorization: Bearer <jwt>` (guard 'jwt'). RBAC en
`/api/admin/users` (@require_roles admin) y ABAC en update/delete de notas (Gate, dentro del
service). Mismas reglas que el carril web; lo único que cambia es el mecanismo de auth.
"""

from __future__ import annotations

from typing import Any, cast

from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy import select

from app.Core.Auth import Auth, Authenticatable, Hash, guarded, require_roles
from app.Core.Database import current_session, transactional
from app.Core.Errors import ConflictError, UnauthorizedError
from app.Core.Http import Controller, Delete, Get, Post, Put
from app.Models.User import User
from app.Modules.Demo.Policies import register_policies
from app.Modules.Demo.Repositories.NoteRepository import NoteRepository
from app.Modules.Demo.Repositories.UserRepository import UserRepository
from app.Modules.Demo.Serializers import note_dict, user_dict
from app.Modules.Demo.Services.NoteService import NoteService

register_policies()  # registra las abilities ABAC (note.update / note.delete)

# Guards explícitos: este carril es SIEMPRE JWT (la app sirve los dos carriles a la vez).
_JwtUser = Depends(guarded("jwt"))
_AdminJwt = Depends(require_roles("admin", guard="jwt"))


class RegisterInput(BaseModel):
    name: str = ""
    email: str
    password: str


class LoginInput(BaseModel):
    email: str
    password: str


class NoteInput(BaseModel):
    title: str
    body: str = ""


@transactional
def _create_user(name: str, email: str, password: str) -> dict[str, Any]:
    if current_session().execute(select(User).where(User.email == email)).scalars().first() is not None:
        raise ConflictError("El email ya está registrado.", details={"email": email})
    user = User(name=name, email=email, password=Hash.make(password), roles="")
    current_session().add(user)
    current_session().flush()
    return user_dict(user)


@Controller("/api", tags=["demo-api"])
class ApiController:
    @Post("/register", status_code=201)
    def register(self, body: RegisterInput) -> dict[str, Any]:
        return _create_user(body.name, body.email, body.password)

    @Post("/login")
    def login(self, body: LoginInput) -> dict[str, str]:
        token = Auth.attempt(body.email, body.password)
        if token is None:
            raise UnauthorizedError("Credenciales inválidas.")
        return {"access_token": token, "token_type": "bearer"}

    @Get("/me")
    def me(self, user: Authenticatable = _JwtUser) -> dict[str, Any]:
        return user_dict(cast("User", user))

    @Get("/notes")
    def list_notes(self, user: Authenticatable = _JwtUser) -> list[dict[str, Any]]:
        return [note_dict(note) for note in NoteRepository().for_owner(user.get_auth_identifier())]

    @Post("/notes", status_code=201)
    def create_note(self, body: NoteInput, user: Authenticatable = _JwtUser) -> dict[str, Any]:
        return NoteService().create(user.get_auth_identifier(), body.title, body.body)

    @Put("/notes/{note_id}")
    def update_note(self, note_id: int, body: NoteInput, user: Authenticatable = _JwtUser) -> dict[str, Any]:
        return NoteService().update(note_id, title=body.title, body=body.body, actor=user)

    @Delete("/notes/{note_id}", status_code=204)
    def delete_note(self, note_id: int, user: Authenticatable = _JwtUser) -> None:
        NoteService().delete(note_id, actor=user)

    @Get("/admin/users")
    def admin_users(self, user: Authenticatable = _AdminJwt) -> list[dict[str, Any]]:
        return [user_dict(person) for person in UserRepository().all()]
