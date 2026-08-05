"""Gateway SQLAlchemy que implementa `MateriaRepositoryPort`."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.banco_preguntas.entities.materia import Materia
from src.banco_preguntas.entities.ports.materia_repository_port import MateriaRepositoryPort
from src.banco_preguntas.frameworks.db.models import MateriaModel


class SQLAlchemyMateriaRepository(MateriaRepositoryPort):
    """Persiste y recupera materias usando SQLAlchemy async."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async a usar en las operaciones."""
        self._session = session

    async def guardar(self, materia: Materia) -> None:
        """Guarda una materia nueva."""
        self._session.add(MateriaModel(id=materia.id, nombre=materia.nombre))
        await self._session.commit()

    async def obtener_por_nombre(self, nombre: str) -> Materia | None:
        """Busca una materia por nombre, o `None` si no existe (INV-BP-00)."""
        resultado = await self._session.execute(
            select(MateriaModel).where(MateriaModel.nombre == nombre)
        )
        modelo = resultado.scalar_one_or_none()
        if modelo is None:
            return None
        return Materia(id=modelo.id, nombre=modelo.nombre)

    async def obtener_por_id(self, materia_id: UUID) -> Materia | None:
        """Busca una materia por id, o `None` si no existe."""
        modelo = await self._session.get(MateriaModel, materia_id)
        if modelo is None:
            return None
        return Materia(id=modelo.id, nombre=modelo.nombre)
