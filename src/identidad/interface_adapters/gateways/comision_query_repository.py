"""Gateway SQLAlchemy que implementa `ComisionQueryPort` (`US-4.2.2`)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.identidad.entities.comision import Comision
from src.identidad.entities.ports.comision_query_port import ComisionQueryPort, EstudianteResumen
from src.identidad.frameworks.db.models import (
    ComisionModel,
    EstudianteModel,
    UsuarioModel,
    comision_docentes,
)


class SQLAlchemyComisionQueryRepository(ComisionQueryPort):
    """Consulta comisiones por materia y estudiantes por comisión usando SQLAlchemy async."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async a usar en las consultas."""
        self._session = session

    async def listar_comisiones_por_materia(
        self, materia_id: UUID, incluir_inactivas: bool = False
    ) -> list[Comision]:
        """Lista las comisiones de una materia, con sus docentes asignados.

        Materia sin comisiones → lista vacía. Carga `docentes` con `selectinload` —
        necesario en SQLAlchemy async para evitar `MissingGreenlet` al acceder a la
        relación fuera de la sesión (`US-ADJ-23`). `incluir_inactivas=True` también trae las
        deshabilitadas — lo usa la pantalla de gestión de Comisiones del Administrador; el
        resto de los consumidores (Docente, Analytics) sigue viendo solo las activas.
        """
        condiciones = [ComisionModel.materia_id == materia_id]
        if not incluir_inactivas:
            condiciones.append(ComisionModel.activa.is_(True))
        query = (
            select(ComisionModel).where(*condiciones).options(selectinload(ComisionModel.docentes))
        )
        resultado = await self._session.execute(query)
        return [
            Comision(
                id=modelo.id,
                materia_id=modelo.materia_id,
                horario=modelo.horario,
                administrador_id=modelo.administrador_id,
                docentes_asignados=[docente.id for docente in modelo.docentes],
                activa=modelo.activa,
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

    async def tiene_comisiones_asignadas(self, docente_id: UUID) -> bool:
        """Indica si el docente está asignado a alguna comisión (activa o no)."""
        query = (
            select(comision_docentes.c.comision_id)
            .where(comision_docentes.c.docente_id == docente_id)
            .limit(1)
        )
        resultado = await self._session.execute(query)
        return resultado.first() is not None

    async def tiene_comisiones_creadas(self, administrador_id: UUID) -> bool:
        """Indica si el administrador creó alguna comisión (activa o no)."""
        query = (
            select(ComisionModel.id)
            .where(ComisionModel.administrador_id == administrador_id)
            .limit(1)
        )
        resultado = await self._session.execute(query)
        return resultado.first() is not None
