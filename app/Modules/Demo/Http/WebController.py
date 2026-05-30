"""Carril WEB del demo: server-rendered con HTMX + Alpine + Pico.css, auth por SESIÓN cookie
(+ CSRF). Para frontends de primera-parte (sin Inertia: HTMX cubre la interactividad).

No autenticado → redirect a /login (browser-friendly, en vez del 401 JSON del carril API).
Las mutaciones post-login (crear/borrar nota, salir) van por HTMX → el layout reenvía el token
CSRF en cada request. Login/registro son forms normales (aún sin sesión → CSRF exento).
"""

from __future__ import annotations

from typing import cast

from fastapi import Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from app.Core.Auth import Auth, set_current_user
from app.Core.Auth.Guards import SessionGuard
from app.Core.Config import settings
from app.Core.Errors import ConflictError
from app.Core.Http import Controller, Get, Post
from app.Core.View import view
from app.Models.User import User
from app.Modules.Demo.Policies import register_policies
from app.Modules.Demo.Repositories.NoteRepository import NoteRepository
from app.Modules.Demo.Repositories.UserRepository import UserRepository
from app.Modules.Demo.Services.NoteService import NoteService
from app.Modules.Demo.Services.UserService import UserService

register_policies()


def _web_user(request: Request) -> User | None:
    """Resuelve el usuario de la sesión-cookie (o None) y lo fija en el contextvar."""
    user = SessionGuard().authenticate(request)
    set_current_user(user)
    return cast("User | None", user)


def _page(name: str, *, user: User | None = None, **context: object) -> HTMLResponse:
    """Render con el contexto común (user + nombres de CSRF para el layout)."""
    return view(
        name, {"user": user, "csrf_cookie": settings.csrf_cookie, "csrf_header": settings.csrf_header, **context}
    )


def _notes_fragment(user: User) -> HTMLResponse:
    """Solo la lista de notas (para los swaps de HTMX)."""
    return view("demo/_notes", {"notes": NoteRepository().for_owner(user.get_auth_identifier())})


@Controller("", tags=["demo-web"])
class WebController:
    @Get("/")
    def home(self, request: Request) -> Response:
        return RedirectResponse("/notes" if _web_user(request) else "/login", status_code=303)

    @Get("/login")
    def login_form(self, request: Request) -> HTMLResponse:
        return _page("demo/login", error=None)

    @Post("/login")
    def login_submit(self, request: Request, email: str = Form(...), password: str = Form(...)) -> Response:
        user = Auth.validate_credentials(email, password)
        if user is None:
            return _page("demo/login", error="Credenciales inválidas.")
        Auth.login(request, user)
        return RedirectResponse("/notes", status_code=303)

    @Get("/register")
    def register_form(self, request: Request) -> HTMLResponse:
        return _page("demo/register", error=None)

    @Post("/register")
    def register_submit(
        self, request: Request, name: str = Form(""), email: str = Form(...), password: str = Form(...)
    ) -> Response:
        try:
            created = UserService().register(name, email, password)
        except ConflictError:
            return _page("demo/register", error="Ese email ya está registrado.")
        request.session["user_id"] = str(created["id"])  # login inmediato
        return RedirectResponse("/notes", status_code=303)

    @Post("/logout")
    def logout(self, request: Request) -> Response:
        Auth.logout(request)
        return Response(status_code=204, headers={"HX-Redirect": "/login"})  # HTMX redirige

    @Get("/notes")
    def notes_page(self, request: Request) -> Response:
        user = _web_user(request)
        if user is None:
            return RedirectResponse("/login", status_code=303)
        return _page("demo/notes", user=user, notes=NoteRepository().for_owner(user.get_auth_identifier()))

    @Post("/notes")
    def create_note(self, request: Request, title: str = Form(...), body: str = Form("")) -> Response:
        user = _web_user(request)
        if user is None:
            return Response(status_code=401, headers={"HX-Redirect": "/login"})
        NoteService().create(user.get_auth_identifier(), title, body)
        return _notes_fragment(user)

    @Post("/notes/{note_id}/delete")
    def delete_note(self, request: Request, note_id: int) -> Response:
        user = _web_user(request)
        if user is None:
            return Response(status_code=401, headers={"HX-Redirect": "/login"})
        NoteService().delete(note_id, actor=user)  # ABAC: solo el dueño (Gate)
        return _notes_fragment(user)

    @Get("/admin/users")
    def admin_users(self, request: Request) -> Response:
        user = _web_user(request)
        if user is None:
            return RedirectResponse("/login", status_code=303)
        if "admin" not in user.get_roles():  # RBAC
            forbidden = _page("demo/forbidden", user=user)
            forbidden.status_code = 403
            return forbidden
        return _page("demo/admin_users", user=user, users=UserRepository().all())
