"""Gateway SQLAlchemy que implementa `ComisionQueryPort` (`US-4.2.2`)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.identidad.entities.comision import Comision
from src.identidad.entities.ports.comision_query_port import ComisionQueryPort, EstudianteResumen
from src.identidad.frameworks.db.models import ComisionModel, EstudianteModel, UsuarioModel


class SQLAlchemyComisionQueryRepository(ComisionQueryPort):
    """Consulta comisiones por materia y estudiantes por comisión usando SQLAlchemy async."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async a usar en las consultas."""
        self._session = session

    async def listar_comisiones_por_materia(self, materia_id: UUID) -> list[Comision]:
        """Lista las comisiones de una materia, con sus docentes asignados. Materia sin
        comisiones → lista vacía.

        Carga `docentes` con `selectinload` — necesario en SQLAlchemy async para evitar
        `MissingGreenlet` al acceder a la relación fuera de la sesión (`US-ADJ-23`).
        """
        query = (
            select(ComisionModel)
            .where(ComisionModel.materia_id == materia_id)
            .options(selectinload(ComisionModel.docentes))
        )
        resultado = await self._session.execute(query)
        return [
            Comision(
                id=modelo.id,
                materia_id=modelo.materia_id,
                horario=modelo.horario,
                administrador_id=modelo.administrador_id,
                docentes_asignados=[docente.id for docente in modelo.docentes],
            )
            for modelo in resultado.scalars().all()
        ]

    async def listar_estudiantes(self, comision_id: UUID) -> list[EstudianteResumen]:
        """Lista los estudiantes inscriptos en una comisión. Sin inscriptos → lista vacía."""
        query = (
            select(UsuarioModel)
            .join(EstudianteModel, EstudianteModel.id == UsuarioModel.id)
            .where(EstudianteModel.comision_id == comision_id)
        )
        resultado = await self._session.execute(query)
        return [
            EstudianteResumen(id=modelo.id, nombre=modelo.nombre)
            for modelo in resultado.scalars().all()
        ]
