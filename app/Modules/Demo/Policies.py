"""Policies (ABAC) del demo: una nota solo la edita/borra su DUEÑO.

`register_policies()` registra las abilities en el Gate (lo llaman los controllers al importarse).
"""

from __future__ import annotations

from typing import Any

from app.Core.Auth import Authenticatable, Gate


def _is_owner(user: Authenticatable | None, note: Any) -> bool:
    return user is not None and getattr(note, "owner_id", None) == user.get_auth_identifier()


def register_policies() -> None:
    Gate.define("note.update", _is_owner)
    Gate.define("note.delete", _is_owner)
