"""Gateway SQLAlchemy que implementa `ComisionRepositoryPort`."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.identidad.entities.comision import Comision
from src.identidad.entities.ports.comision_repository_port import ComisionRepositoryPort
from src.identidad.frameworks.db.models import ComisionModel, DocenteModel


class SQLAlchemyComisionRepository(ComisionRepositoryPort):
    """Persiste y recupera comisiones usando SQLAlchemy async."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async a usar en las operaciones."""
        self._session = session

    async def guardar(self, comision: Comision) -> None:
        """Persiste una comisión nueva."""
        self._session.add(
            ComisionModel(
                id=comision.id,
                materia=comision.materia,
                horario=comision.horario,
                administrador_id=comision.administrador_id,
            )
        )
        await self._session.commit()

    async def obtener_por_id(self, comision_id: UUID) -> Comision | None:
        """Busca una comisión por id junto con sus docentes, o `None` si no existe."""
        modelo = await self._session.get(
            ComisionModel, comision_id, options=[selectinload(ComisionModel.docentes)]
        )
        if modelo is None:
            return None
        return Comision(
            id=modelo.id,
            materia=modelo.materia,
            horario=modelo.horario,
            administrador_id=modelo.administrador_id,
            docentes_asignados=[docente.id for docente in modelo.docentes],
        )

    async def actualizar(self, comision: Comision) -> None:
        """Persiste los docentes nuevos asignados a una comisión existente."""
        modelo = await self._session.get(
            ComisionModel, comision.id, options=[selectinload(ComisionModel.docentes)]
        )
        if modelo is None:
            raise ValueError(f"Comisión '{comision.id}' no existe.")

        ids_actuales = {docente.id for docente in modelo.docentes}
        for docente_id in comision.docentes_asignados:
            if docente_id not in ids_actuales:
                docente_model = await self._session.get(DocenteModel, docente_id)
                if docente_model is not None:
                    modelo.docentes.append(docente_model)

        await self._session.commit()
