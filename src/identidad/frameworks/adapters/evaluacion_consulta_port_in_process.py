"""Adaptador de `EvaluacionConsultaPort` — llamada in-process a BC Actividad Evaluativa.

Mismo criterio de acoplamiento consciente (`ADR-006`) que `materia_port_in_process.py`:
vive en `frameworks/` de Identidad, nunca en `entities/` ni `use_cases/`. Consulta
directamente `EventoModel` (event store ajeno), sin invocar ningún Use Case de esa BC —
mismo patrón que `EvaluacionDesempenoConsultaPortInProcess` de Analytics, que también filtra
el payload en memoria (sin operadores JSONB en la query) por consistencia con el resto del
proyecto.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.actividad_evaluativa.frameworks.db.models import EventoModel
from src.identidad.entities.ports.evaluacion_consulta_port import EvaluacionConsultaPort

AGGREGATE_TYPE_EVALUACION = "Evaluacion"
EVENT_TYPE_INICIADA = "EvaluacionIniciada"


class EvaluacionConsultaPortInProcess(EvaluacionConsultaPort):
    """Implementa `EvaluacionConsultaPort` consultando el event store de Actividad Evaluativa."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async compartida con el event store de Actividad Evaluativa."""
        self._session = session

    async def tiene_evaluaciones(self, estudiante_id: UUID) -> bool:
        """Indica si el estudiante inició alguna vez una evaluación (cualquier estado)."""
        query = select(EventoModel.payload).where(
            EventoModel.aggregate_type == AGGREGATE_TYPE_EVALUACION,
            EventoModel.event_type == EVENT_TYPE_INICIADA,
        )
        resultado = await self._session.execute(query)
        estudiante_id_str = str(estudiante_id)
        return any(payload["estudiante_id"] == estudiante_id_str for payload in resultado.scalars())
