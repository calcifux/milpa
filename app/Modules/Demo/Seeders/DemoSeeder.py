"""Seeder del demo: ~100 usuarios con ROLES variados (para probar RBAC/ABAC a fondo) +
muchas notas de Ana (para el scroll infinito). Idempotente. Todos usan password "password".
"""

from __future__ import annotations

from sqlalchemy import select

from app.Core.Auth import Hash
from app.Core.Database import current_session
from app.Core.Database.Seeder import Seeder
from app.Models.Note import Note
from app.Models.User import User

# Mezcla de roles para los usuarios generados (la mayoría normales; algunos viewer/editor/admin).
_ROLE_CYCLE = ["", "", "", "viewer", "", "editor", "", "", "viewer", "admin"]


class DemoSeeder(Seeder):
    def run(self) -> None:
        session = current_session()
        if session.execute(select(User).limit(1)).first() is not None:
            return  # ya sembrado: no duplicar

        password = Hash.make("password")  # se hashea UNA vez (todos comparten password en el demo)

        # Logins conocidos. Ana es 'editor' (modera): el ABAC la deja editar notas ajenas.
        admin = User(name="Admin", email="admin@demo.test", password=password, roles="admin")
        ana = User(name="Ana", email="ana@demo.test", password=password, roles="editor")
        beto = User(name="Beto", email="beto@demo.test", password=password, roles="")
        session.add_all([admin, ana, beto])

        # 97 usuarios generados con roles variados (total 100) — para RBAC y para el scroll.
        generated = [
            User(
                name=f"Usuario {i:03d}",
                email=f"user{i:03d}@demo.test",
                password=password,
                roles=_ROLE_CYCLE[i % len(_ROLE_CYCLE)],
            )
            for i in range(1, 98)
        ]
        session.add_all(generated)
        session.flush()  # asigna ids (para owner_id)

        # Ana con muchas notas (scroll infinito) + una de Beto.
        notes = [
            Note(owner_id=ana.id, title=f"Nota de Ana #{i:02d}", body=f"Contenido de la nota número {i}.")
            for i in range(1, 24)
        ]
        notes.append(Note(owner_id=beto.id, title="Idea de Beto", body="Probar milpa este finde"))
        session.add_all(notes)
