"""Adaptador de `EvaluacionConsultaPort` — llamada in-process a BC Actividad Evaluativa.

Mismo criterio de acoplamiento consciente (`ADR-006`) que `materia_port_in_process.py`:
vive en `frameworks/` de Identidad, nunca en `entities/` ni `use_cases/`. Delega en el gateway
de consulta que expone Actividad Evaluativa (`EstudianteEvaluacionesQueryPort`); no lee el event
store ni sus modelos ORM (`US-9.4.3`, `ADR-026`).
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.actividad_evaluativa.frameworks.adapters.estudiante_evaluaciones_query_repository import (
    SQLAlchemyEstudianteEvaluacionesQueryRepository,
)
from src.identidad.entities.ports.evaluacion_consulta_port import EvaluacionConsultaPort


class EvaluacionConsultaPortInProcess(EvaluacionConsultaPort):
    """Implementa `EvaluacionConsultaPort` consultando a Actividad Evaluativa por su puerto."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async compartida con Actividad Evaluativa."""
        self._evaluaciones_query = SQLAlchemyEstudianteEvaluacionesQueryRepository(session)

    async def tiene_evaluaciones(self, estudiante_id: UUID) -> bool:
        """Indica si el estudiante inició alguna vez una evaluación (cualquier estado)."""
        return await self._evaluaciones_query.tiene_evaluaciones_iniciadas(estudiante_id)
