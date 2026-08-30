"""Gateway SQLAlchemy que implementa `ActividadQueryPort` (`US-3.4.2`).

Agrupa los eventos crudos de la tabla `events` en memoria en vez de mantener una tabla de
proyección sincronizada aparte — mismo criterio de diseño que
`SQLAlchemyEvaluacionActivaQueryRepository` (`US-3.2.4`): válido a la escala de 30-60
alumnos/comisión, documentado como reversible si el volumen cambia.
"""

from __future__ import annotations

from itertools import groupby
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.actividad_evaluativa.entities.actividad_evaluativa_periodo_abierto import (
    ActividadEvaluativaPeriodoAbierto,
)
from src.actividad_evaluativa.entities.ports.actividad_query_port import (
    ActividadQueryPort,
    ActividadResumen,
)
from src.actividad_evaluativa.entities.ports.event_store_port import EventoAlmacenado
from src.actividad_evaluativa.frameworks.db.models import EventoModel

AGGREGATE_TYPE_ACTIVIDAD = "ActividadEvaluativaPeriodoAbierto"
AGGREGATE_TYPE_EVALUACION = "Evaluacion"

_EVENT_TYPE_FINALIZADA = "EvaluacionFinalizada"


class SQLAlchemyActividadQueryRepository(ActividadQueryPort):
    """Deriva el resumen de cada actividad de una materia agrupando `events` en memoria."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async a usar en la consulta."""
        self._session = session

    async def listar_por_materia(self, materia_id: UUID) -> list[ActividadResumen]:
        """Reconstruye cada actividad de `materia_id` y le suma el conteo de evaluaciones."""
        actividades = await self._cargar_actividades_de_materia(materia_id)
        conteos = await self._contar_evaluaciones({actividad.id for actividad in actividades})
        return [_a_resumen(actividad, conteos) for actividad in actividades]

    async def _cargar_actividades_de_materia(
        self, materia_id: UUID
    ) -> list[ActividadEvaluativaPeriodoAbierto]:
        """Reconstruye cada `ActividadEvaluativaPeriodoAbierto` del BC y filtra por materia."""
        resultado = await self._session.execute(
            select(EventoModel)
            .where(EventoModel.aggregate_type == AGGREGATE_TYPE_ACTIVIDAD)
            .order_by(EventoModel.aggregate_id, EventoModel.sequence_number)
        )
        modelos = resultado.scalars().all()

        actividades = []
        for _, grupo_iter in groupby(modelos, key=lambda modelo: modelo.aggregate_id):
            eventos = [_a_evento_almacenado(modelo) for modelo in grupo_iter]
            actividad = ActividadEvaluativaPeriodoAbierto.reconstruir(eventos)
            if actividad.materia_id == materia_id:
                actividades.append(actividad)
        return actividades

    async def _contar_evaluaciones(self, actividad_ids: set[UUID]) -> dict[UUID, tuple[int, int]]:
        """Cuenta evaluaciones (activas, finalizadas) por `actividad_id`, agrupando en memoria."""
        if not actividad_ids:
            return {}

        resultado = await self._session.execute(
            select(EventoModel)
            .where(EventoModel.aggregate_type == AGGREGATE_TYPE_EVALUACION)
            .order_by(EventoModel.aggregate_id, EventoModel.sequence_number)
        )
        modelos = resultado.scalars().all()

        conteos: dict[UUID, tuple[int, int]] = {}
        for _, grupo_iter in groupby(modelos, key=lambda modelo: modelo.aggregate_id):
            eventos = list(grupo_iter)
            actividad_id = UUID(eventos[0].payload["actividad_id"])
            if actividad_id not in actividad_ids:
                continue
            activas, finalizadas = conteos.get(actividad_id, (0, 0))
            if eventos[-1].event_type == _EVENT_TYPE_FINALIZADA:
                finalizadas += 1
            else:
                activas += 1
            conteos[actividad_id] = (activas, finalizadas)
        return conteos


def _a_evento_almacenado(modelo: EventoModel) -> EventoAlmacenado:
    """Adapta un `EventoModel` (fila ORM) a `EventoAlmacenado` (tipo de dominio)."""
    return EventoAlmacenado(
        sequence_number=modelo.sequence_number,
        event_type=modelo.event_type,
        payload=modelo.payload,
        occurred_at=modelo.occurred_at,
    )


def _a_resumen(
    actividad: ActividadEvaluativaPeriodoAbierto, conteos: dict[UUID, tuple[int, int]]
) -> ActividadResumen:
    """Arma el `ActividadResumen` de una actividad ya reconstruida."""
    activas, finalizadas = conteos.get(actividad.id, (0, 0))
    return ActividadResumen(
        id=actividad.id,
        materia_id=actividad.materia_id,
        titulo=actividad.titulo,
        fecha_apertura=actividad.fecha_apertura,
        fecha_cierre=actividad.fecha_cierre,
        cantidad_preguntas=actividad.cantidad_preguntas,
        cantidad_intentos_permitidos=actividad.cantidad_intentos_permitidos,
        cerrada_manualmente=actividad.cerrada_manualmente,
        cantidad_evaluaciones_activas=activas,
        cantidad_evaluaciones_finalizadas=finalizadas,
    )
