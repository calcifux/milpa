"""Base de repositorios tipada, estilo `JpaRepository<Model, Id>` de Spring Data.

Heredar de `Repository[Model, Id]` te da:
  - CRUD comun GRATIS y TIPADO: `get(id) -> Model | None`, `all()`, `add()`, `delete()`.
  - `self.session` (la sesion AMBIENTE encapsulada) para las queries CUSTOM, en vez de
    llamar `current_session()` a mano.
  - Auto-gestion de sesion: los metodos publicos son @auto_session (lecturas) — funcionan
    CON o SIN `session_scope`; el dev no envuelve nada. `add`/`delete` son @transactional
    (escriben -> commitean, o se unen a la tx de afuera).

Ejemplo:

    class CompanyRepository(Repository[Company, int]):
        model = Company
        def find_subastador(self) -> Company | None:           # query custom
            return self.session.execute(select(Company).where(...)).scalars().first()

    CompanyRepository().get(7)              # heredado, tipado Company | None, sin scope

LIMITE (honesto): no derivamos queries desde el NOMBRE del metodo (el `findByX` de
Spring Data usa proxies en runtime; en Python seria metaprogramacion fragil). Las
queries custom llevan cuerpo, pero usan `self.session`.
"""

from __future__ import annotations

from collections.abc import Sequence
from types import FunctionType
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.Core.Database.Transactional import auto_session, current_session, transactional
from app.Core.Errors import ResourceNotFoundError


class Repository[ModelT, IdT]:
    """Base CRUD tipada por (modelo, tipo de id). La subclase fija `model`."""

    model: type[ModelT]

    @property
    def session(self) -> Session:
        """La sesion AMBIENTE (la abre @auto_session/@transactional). Encapsula
        `current_session()` para que las queries custom no lo llamen directo."""
        return current_session()

    @auto_session
    def get(self, entity_id: IdT) -> ModelT | None:
        return self.session.get(self.model, entity_id)

    @auto_session
    def find_or_fail(self, entity_id: IdT) -> ModelT:
        """Como `get`, pero NUNCA devuelve None: si no existe, lanza `ResourceNotFoundError`
        (= `findOrFail` de Eloquent / `getReferenceById` que falla en Spring Data). El
        handler global la traduce a un 404 JSON; el service no tiene que checar None a mano."""
        entity = self.session.get(self.model, entity_id)
        if entity is None:
            raise ResourceNotFoundError(
                f"{self.model.__name__} con id {entity_id!r} no existe",
                details={"model": self.model.__name__, "id": str(entity_id)},
            )
        return entity

    @auto_session
    def all(self) -> Sequence[ModelT]:
        return self.session.execute(select(self.model)).scalars().all()

    @transactional
    def add(self, entity: ModelT) -> ModelT:
        self.session.add(entity)
        self.session.flush()  # asigna PK/defaults sin esperar al commit
        return entity

    @transactional
    def delete(self, entity: ModelT) -> None:
        self.session.delete(entity)

    @transactional
    def first_or_create(self, where: dict[str, Any], values: dict[str, Any] | None = None) -> ModelT:
        """Busca la PRIMERA fila que cumpla `where`; si no hay, la CREA con `where + values`
        (= `firstOrCreate` de Eloquent). `where` son las columnas de búsqueda/identidad;
        `values` son extras solo-al-crear. Es @transactional: si crea, persiste (o se une a
        la tx de afuera). Devuelve la entidad existente o la recién creada (con su PK)."""
        existing = self.session.execute(select(self.model).filter_by(**where)).scalars().first()
        if existing is not None:
            return existing
        entity = self.model(**{**where, **(values or {})})
        self.session.add(entity)
        self.session.flush()  # asigna PK/defaults sin esperar al commit
        return entity

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Los metodos CUSTOM (queries) de la subclase: auto_session (con o sin scope).
        # El CRUD heredado ya viene decorado en la base; aqui solo lo propio de la subclase.
        for name, attribute in list(vars(cls).items()):
            if isinstance(attribute, FunctionType) and not name.startswith("_"):
                setattr(cls, name, auto_session(attribute))
