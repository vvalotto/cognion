"""Gateway SQLAlchemy que implementa `MateriaRepositoryPort`."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.banco_preguntas.entities.materia import Materia
from src.banco_preguntas.entities.ports.materia_repository_port import MateriaRepositoryPort
from src.banco_preguntas.frameworks.db.models import BancoModel, MateriaModel


class SQLAlchemyMateriaRepository(MateriaRepositoryPort):
    """Persiste y recupera materias usando SQLAlchemy async."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async a usar en las operaciones."""
        self._session = session

    async def guardar(self, materia: Materia) -> None:
        """Guarda una materia nueva."""
        self._session.add(MateriaModel(id=materia.id, nombre=materia.nombre))
        await self._session.commit()

    async def actualizar(self, materia: Materia) -> None:
        """Guarda cambios sobre una materia existente (nombre y `activa`)."""
        modelo = await self._session.get(MateriaModel, materia.id)
        if modelo is None:
            return
        modelo.nombre = materia.nombre
        modelo.activa = materia.activa
        await self._session.commit()

    async def eliminar(self, materia_id: UUID) -> None:
        """Borra físicamente una materia sin preguntas ni comisiones asociadas.

        Borra también su `Banco` (INV-BP-01: 1:1, siempre vacío en este punto — el caso de
        uso ya validó que no hay preguntas) para no violar la FK `banco.materia_id`.
        """
        modelo = await self._session.get(MateriaModel, materia_id)
        if modelo is None:
            return
        resultado_banco = await self._session.execute(
            select(BancoModel).where(BancoModel.materia_id == materia_id)
        )
        banco_modelo = resultado_banco.scalar_one_or_none()
        if banco_modelo is not None:
            await self._session.delete(banco_modelo)
        await self._session.delete(modelo)
        await self._session.commit()

    async def obtener_por_nombre(self, nombre: str) -> Materia | None:
        """Busca una materia por nombre, o `None` si no existe (INV-BP-00)."""
        resultado = await self._session.execute(
            select(MateriaModel).where(MateriaModel.nombre == nombre)
        )
        modelo = resultado.scalar_one_or_none()
        if modelo is None:
            return None
        return Materia(id=modelo.id, nombre=modelo.nombre, activa=modelo.activa)

    async def obtener_por_id(self, materia_id: UUID) -> Materia | None:
        """Busca una materia por id, o `None` si no existe."""
        modelo = await self._session.get(MateriaModel, materia_id)
        if modelo is None:
            return None
        return Materia(id=modelo.id, nombre=modelo.nombre, activa=modelo.activa)

    async def listar(self, incluir_inactivas: bool = False) -> list[Materia]:
        """Lista las materias activas; con `incluir_inactivas=True`, también las deshabilitadas."""
        query = select(MateriaModel)
        if not incluir_inactivas:
            query = query.where(MateriaModel.activa.is_(True))
        resultado = await self._session.execute(query)
        return [
            Materia(id=modelo.id, nombre=modelo.nombre, activa=modelo.activa)
            for modelo in resultado.scalars()
        ]
