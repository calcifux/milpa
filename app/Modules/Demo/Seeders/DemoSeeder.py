"""Seeder del demo: ~100 usuarios con NOMBRES variados (nombre + apellido) y ROLES variados
(para probar RBAC/ABAC a fondo) + muchas notas de Ana (para el scroll infinito). Idempotente.
Todos usan password "password".
"""

from __future__ import annotations

import unicodedata

from sqlalchemy import select

from app.Core.Auth import Hash
from app.Core.Database import current_session
from app.Core.Database.Seeder import Seeder
from app.Models.Note import Note
from app.Models.User import User

# Mezcla de roles para los usuarios generados (la mayoría normales; algunos viewer/editor/admin).
_ROLE_CYCLE = ["", "", "", "viewer", "", "editor", "", "", "viewer", "admin"]

_FIRST_NAMES = [
    "Lucía",
    "Mateo",
    "Sofía",
    "Diego",
    "Valentina",
    "Santiago",
    "Camila",
    "Sebastián",
    "Renata",
    "Emiliano",
    "Regina",
    "Leonardo",
    "Ximena",
    "Daniel",
    "Victoria",
    "Adrián",
    "Fernanda",
    "Gabriel",
    "Mariana",
    "Andrés",
    "Paula",
    "Tomás",
    "Isabela",
    "Nicolás",
    "Lorenzo",
]
_LAST_NAMES = [
    "García",
    "Martínez",
    "López",
    "Hernández",
    "González",
    "Rodríguez",
    "Pérez",
    "Sánchez",
    "Ramírez",
    "Cruz",
    "Flores",
    "Gómez",
    "Díaz",
    "Reyes",
    "Morales",
    "Ortiz",
    "Gutiérrez",
    "Chávez",
    "Ramos",
    "Vázquez",
    "Castillo",
    "Jiménez",
    "Romero",
    "Aguilar",
    "Mendoza",
]


def _ascii(text: str) -> str:
    """Quita acentos y baja a minúsculas (para emails ASCII): 'Lucía' -> 'lucia'."""
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower()


class DemoSeeder(Seeder):
    def run(self) -> None:
        session = current_session()
        if session.execute(select(User).limit(1)).first() is not None:
            return  # ya sembrado: no duplicar

        password = Hash.make("password")  # se hashea UNA vez (todos comparten password en el demo)

        # Logins conocidos. Ana es 'editor' (modera): el ABAC la deja editar notas ajenas.
        admin = User(name="Admin Demo", email="admin@demo.test", password=password, roles="admin")
        ana = User(name="Ana López", email="ana@demo.test", password=password, roles="editor")
        beto = User(name="Beto Ramírez", email="beto@demo.test", password=password, roles="")
        session.add_all([admin, ana, beto])

        # 97 usuarios generados con nombres y roles variados (total 100) — para RBAC, búsqueda y scroll.
        generated = []
        for i in range(1, 98):
            first = _FIRST_NAMES[i % len(_FIRST_NAMES)]
            last = _LAST_NAMES[(i * 3) % len(_LAST_NAMES)]  # *3 desfasa nombre y apellido
            generated.append(
                User(
                    name=f"{first} {last}",
                    email=f"{_ascii(first)}.{_ascii(last)}{i}@demo.test",  # i => email único
                    password=password,
                    roles=_ROLE_CYCLE[i % len(_ROLE_CYCLE)],
                )
            )
        session.add_all(generated)
        session.flush()  # asigna ids (para owner_id)

        # Ana con muchas notas (scroll infinito) + una de Beto.
        notes = [
            Note(owner_id=ana.id, title=f"Nota de Ana #{i:02d}", body=f"Contenido de la nota número {i}.")
            for i in range(1, 24)
        ]
        notes.append(Note(owner_id=beto.id, title="Idea de Beto", body="Probar milpa este finde"))
        session.add_all(notes)
