"""Integración de Alembic con milpa (migraciones de esquema).

La Config de Alembic se arma EN CÓDIGO (sin `alembic.ini` suelto): solo fija el
`script_location` a `migrations/` en la raíz. La conexión y los modelos los resuelve
`migrations/env.py` desde Settings (`DATABASE_URL`) y `Base.metadata`, así no se duplica
ni la config de conexión ni la lista de modelos. Lo opera `jornal migrate ...`
(app/Core/Console/Commands/MigrateCommands.py).

Contra una BD legacy que NO administras, no generes migraciones de tablas ajenas:
usa esto para las tablas NUEVAS del proyecto (greenfield), igual que en Laravel.
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

# migrations/ vive en la RAÍZ del repo. parents[3] desde app/Core/Database/Migrations.py:
#   [0]=Database  [1]=Core  [2]=app  [3]=raíz
_MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "migrations"


def make_alembic_config() -> Config:
    """Config de Alembic sin `.ini`: solo el `script_location` (migrations/). La URL y los
    modelos los resuelve env.py desde Settings/Base (única fuente de verdad)."""
    config = Config()
    config.set_main_option("script_location", str(_MIGRATIONS_DIR))
    return config


def make_revision(message: str, *, autogenerate: bool = True) -> None:
    """Crea una revisión. Con `autogenerate`, compara `Base.metadata` vs el esquema real."""
    command.revision(make_alembic_config(), message=message, autogenerate=autogenerate)


def run_upgrade(revision: str = "head") -> None:
    """Aplica migraciones hasta `revision` (default: `head`, todas las pendientes)."""
    command.upgrade(make_alembic_config(), revision)


def run_downgrade(revision: str = "-1") -> None:
    """Revierte hasta `revision` (default: `-1`, una atrás)."""
    command.downgrade(make_alembic_config(), revision)


def show_current(*, verbose: bool = False) -> None:
    """Imprime la revisión aplicada actualmente en la BD."""
    command.current(make_alembic_config(), verbose=verbose)


def show_history(*, verbose: bool = False) -> None:
    """Imprime el historial de revisiones."""
    command.history(make_alembic_config(), verbose=verbose)
