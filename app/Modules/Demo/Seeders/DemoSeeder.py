"""Seeder del demo: un admin + dos usuarios normales + unas notas. Idempotente."""

from __future__ import annotations

from sqlalchemy import select

from app.Core.Auth import Hash
from app.Core.Database import current_session
from app.Core.Database.Seeder import Seeder
from app.Models.Note import Note
from app.Models.User import User


class DemoSeeder(Seeder):
    def run(self) -> None:
        session = current_session()
        if session.execute(select(User).limit(1)).first() is not None:
            return  # ya sembrado: no duplicar

        password = Hash.make("password")  # demo: todos usan "password"
        admin = User(name="Admin", email="admin@demo.test", password=password, roles="admin")
        ana = User(name="Ana", email="ana@demo.test", password=password, roles="")
        beto = User(name="Beto", email="beto@demo.test", password=password, roles="")
        session.add_all([admin, ana, beto])
        session.flush()  # asigna ids para los owner_id

        session.add_all(
            [
                Note(owner_id=ana.id, title="Nota de Ana", body="Hola desde Ana 👋"),
                Note(owner_id=ana.id, title="Lista del súper", body="Café, pan, tortillas"),
                Note(owner_id=beto.id, title="Idea de Beto", body="Probar milpa este finde"),
            ]
        )
