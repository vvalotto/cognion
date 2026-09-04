"""Adapter que implementa `EvaluacionDesempenoConsultaPort` leyendo el event store ajeno.

Único punto de Analytics que importa código de otro BC — consulta directamente `EventoModel`
de `src.actividad_evaluativa.frameworks.db.models`, no invoca ningún Use Case de esa BC
(decisión documentada en `docs/specs/inc4/US-4.1.1.md` §Contexto del dominio: no existe ahí un
Use Case con esta responsabilidad, y crearlo solo para Analytics ensancharía un BC ajeno).
Mismo criterio de agrupar eventos crudos en memoria, sin proyección sincronizada, que
`SQLAlchemyEvaluacionActivaQueryRepository` (`US-3.2.4`).
"""

from __future__ import annotations

from itertools import groupby
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.actividad_evaluativa.frameworks.db.models import EventoModel
from src.analytics.entities.ports.evaluacion_desempeno_consulta_port import (
    EvaluacionDesempenoConsultaPort,
    EvaluacionDesempenoResumen,
)

AGGREGATE_TYPE_EVALUACION = "Evaluacion"
AGGREGATE_TYPE_ACTIVIDAD = "ActividadEvaluativaPeriodoAbierto"
EVENT_TYPE_INICIADA = "EvaluacionIniciada"
EVENT_TYPE_FINALIZADA = "EvaluacionFinalizada"
EVENT_TYPE_RESPUESTA = "RespuestaRegistrada"


class EvaluacionDesempenoConsultaPortInProcess(EvaluacionDesempenoConsultaPort):
    """Deriva el desempeño de cada `Evaluacion` finalizada agrupando `events` en memoria."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async compartida con el event store de Actividad Evaluativa."""
        self._session = session

    async def listar_evaluaciones_finalizadas(
        self, estudiante_id: UUID, materia_id: UUID | None
    ) -> list[EvaluacionDesempenoResumen]:
        """Ver `EvaluacionDesempenoConsultaPort.listar_evaluaciones_finalizadas`."""
        eventos_evaluacion = await self._eventos_evaluacion_del_estudiante(estudiante_id)
        if not eventos_evaluacion:
            return []

        actividad_ids = {UUID(eventos[0].payload["actividad_id"]) for eventos in eventos_evaluacion}
        materia_por_actividad = await self._materia_por_actividad(actividad_ids)

        resumenes = []
        for eventos in eventos_evaluacion:
            resumen = self._resumen_de_stream(eventos, materia_por_actividad)
            if resumen is None:
                continue
            if materia_id is not None and resumen.materia_id != materia_id:
                continue
            resumenes.append(resumen)
        return resumenes

    async def _eventos_evaluacion_del_estudiante(
        self, estudiante_id: UUID
    ) -> list[list[EventoModel]]:
        """Agrupa los eventos de `Evaluacion` por stream, del Estudiante indicado."""
        resultado = await self._session.execute(
            select(EventoModel)
            .where(EventoModel.aggregate_type == AGGREGATE_TYPE_EVALUACION)
            .order_by(EventoModel.aggregate_id, EventoModel.sequence_number)
        )
        modelos = resultado.scalars().all()

        streams = []
        for _, grupo_iter in groupby(modelos, key=lambda modelo: modelo.aggregate_id):
            eventos = list(grupo_iter)
            primero = eventos[0]
            if primero.event_type != EVENT_TYPE_INICIADA:
                continue
            if primero.payload["estudiante_id"] != str(estudiante_id):
                continue
            streams.append(eventos)
        return streams

    async def _materia_por_actividad(self, actividad_ids: set[UUID]) -> dict[UUID, UUID]:
        """Resuelve `materia_id` de cada `actividad_id` leyendo el primer evento de su stream.

        `materia_id` no cambia después de creada la actividad — no hace falta replay completo.
        """
        if not actividad_ids:
            return {}
        resultado = await self._session.execute(
            select(EventoModel).where(
                EventoModel.aggregate_type == AGGREGATE_TYPE_ACTIVIDAD,
                EventoModel.aggregate_id.in_(actividad_ids),
                EventoModel.sequence_number == 1,
            )
        )
        return {
            modelo.aggregate_id: UUID(modelo.payload["materia_id"])
            for modelo in resultado.scalars().all()
        }

    def _resumen_de_stream(
        self, eventos: list[EventoModel], materia_por_actividad: dict[UUID, UUID]
    ) -> EvaluacionDesempenoResumen | None:
        """Deriva el resumen de un stream ya filtrado por Estudiante, o `None` si no finalizó."""
        evento_finalizada = next(
            (evento for evento in eventos if evento.event_type == EVENT_TYPE_FINALIZADA), None
        )
        if evento_finalizada is None:
            return None

        primero = eventos[0]
        actividad_id = UUID(primero.payload["actividad_id"])
        correctas, incorrectas = _contar_respuestas_vigentes(eventos)

        return EvaluacionDesempenoResumen(
            evaluacion_id=primero.aggregate_id,
            actividad_id=actividad_id,
            materia_id=materia_por_actividad[actividad_id],
            finalizada_en=evento_finalizada.occurred_at,
            cantidad_correctas=correctas,
            cantidad_incorrectas=incorrectas,
        )


def _contar_respuestas_vigentes(eventos: list[EventoModel]) -> tuple[int, int]:
    """Cuenta correctas/incorrectas quedándose con la última `RespuestaRegistrada` por pregunta.

    `eventos` ya viene ordenado por `sequence_number` ascendente — el último evento visto para
    cada `pregunta_id` es siempre el más reciente (INV-AE-09, respuesta vigente).
    """
    es_correcta_por_pregunta: dict[str, bool] = {}
    for evento in eventos:
        if evento.event_type != EVENT_TYPE_RESPUESTA:
            continue
        es_correcta_por_pregunta[evento.payload["pregunta_id"]] = evento.payload["es_correcta"]

    correctas = sum(1 for es_correcta in es_correcta_por_pregunta.values() if es_correcta)
    incorrectas = len(es_correcta_por_pregunta) - correctas
    return correctas, incorrectas
