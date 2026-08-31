"""Caso de uso: inicio de una `Evaluacion` con set aleatorio fijo (US-3.1.3, RF-12)."""

from __future__ import annotations

import random
from datetime import UTC, datetime
from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_periodo_abierto import (
    ActividadEvaluativaPeriodoAbierto,
)
from src.actividad_evaluativa.entities.errors import (
    ActividadNoExiste,
    ConcurrenciaOptimistaError,
    EstudianteNoExiste,
    FueraDePeriodo,
)
from src.actividad_evaluativa.entities.evaluacion import Evaluacion
from src.actividad_evaluativa.entities.eventos import EvaluacionIniciada
from src.actividad_evaluativa.entities.ports.estudiante_consulta_port import (
    EstudianteConsultaPort,
)
from src.actividad_evaluativa.entities.ports.event_store_port import (
    EventoParaAlmacenar,
    EventStorePort,
)
from src.actividad_evaluativa.entities.ports.pregunta_consulta_port import PreguntaConsultaPort

AGGREGATE_TYPE_ACTIVIDAD = "ActividadEvaluativaPeriodoAbierto"
AGGREGATE_TYPE_EVALUACION = "Evaluacion"


class IniciarEvaluacionUseCase:
    """Orquesta el inicio (o la reconexión idempotente) de la `Evaluacion` de un Estudiante."""

    def __init__(
        self,
        estudiante_consulta: EstudianteConsultaPort,
        pregunta_consulta: PreguntaConsultaPort,
        event_store: EventStorePort,
    ) -> None:
        """Recibe los puertos de consulta a Identidad/Banco de Preguntas y el event store."""
        self._estudiante_consulta = estudiante_consulta
        self._pregunta_consulta = pregunta_consulta
        self._event_store = event_store

    async def execute(self, actividad_id: UUID, estudiante_id: UUID) -> tuple[Evaluacion, bool]:
        """Inicia la evaluación, o retoma la existente sin generar un set nuevo (INV-AE-05/06).

        Devuelve `(evaluacion, True)` si esta invocación creó una `Evaluacion` nueva, o
        `(evaluacion, False)` si ya existía una `EnCurso` y se reutilizó tal cual — incluida la
        `Evaluacion` creada por una invocación concurrente que ganó la carrera al insertar el
        primer evento (`US-ADJ-11`). Levanta `EstudianteNoExiste` si el actor no es un
        Estudiante válido, `ActividadNoExiste` si `actividad_id` no tiene stream,
        `FueraDePeriodo` si `ahora` no está dentro de la ventana vigente de la actividad (o está
        cerrada manualmente).
        """
        if not await self._estudiante_consulta.existe(estudiante_id):
            raise EstudianteNoExiste(estudiante_id)

        eventos_actividad = await self._event_store.load(AGGREGATE_TYPE_ACTIVIDAD, actividad_id)
        if not eventos_actividad:
            raise ActividadNoExiste(actividad_id)

        actividad = ActividadEvaluativaPeriodoAbierto.reconstruir(eventos_actividad)
        materia_id = actividad.materia_id
        fecha_apertura = actividad.fecha_apertura
        fecha_cierre = actividad.fecha_cierre
        cantidad_preguntas = actividad.cantidad_preguntas

        ahora = datetime.now(UTC)
        if ahora < fecha_apertura or ahora > fecha_cierre or actividad.cerrada_manualmente:
            raise FueraDePeriodo(actividad_id, ahora)

        evaluacion_id = Evaluacion.id_para(actividad_id, estudiante_id)
        eventos_evaluacion = await self._event_store.load(AGGREGATE_TYPE_EVALUACION, evaluacion_id)
        if eventos_evaluacion:
            return Evaluacion.reconstruir(eventos_evaluacion), False

        ids_disponibles = await self._pregunta_consulta.listar_ids_activas_por_materia(materia_id)
        muestra = random.sample(ids_disponibles, k=cantidad_preguntas)
        preguntas_asignadas = Evaluacion.armar_preguntas_asignadas(muestra)

        evaluacion = Evaluacion.crear(actividad_id, estudiante_id, preguntas_asignadas)
        evento = EvaluacionIniciada(
            evaluacion_id=evaluacion.id,
            actividad_id=actividad_id,
            estudiante_id=estudiante_id,
            preguntas_asignadas=preguntas_asignadas,
        )

        payload = {
            "evaluacion_id": str(evento.evaluacion_id),
            "actividad_id": str(evento.actividad_id),
            "estudiante_id": str(evento.estudiante_id),
            "preguntas_asignadas": [
                {"pregunta_id": str(p.pregunta_id), "orden": p.orden}
                for p in evento.preguntas_asignadas
            ],
            "ocurrido_en": evento.ocurrido_en.isoformat(),
        }
        try:
            await self._event_store.append(
                AGGREGATE_TYPE_EVALUACION,
                evaluacion.id,
                0,
                [EventoParaAlmacenar(event_type="EvaluacionIniciada", payload=payload)],
            )
        except ConcurrenciaOptimistaError:
            # Otra invocación concurrente (mismo Estudiante, misma Actividad) ganó la carrera
            # de insertar el primer evento -- releer y devolver esa Evaluacion en vez de
            # propagar el error (INV-AE-05/06, idempotencia real ante escrituras concurrentes,
            # no solo secuenciales).
            eventos_evaluacion = await self._event_store.load(
                AGGREGATE_TYPE_EVALUACION, evaluacion.id
            )
            return Evaluacion.reconstruir(eventos_evaluacion), False

        return evaluacion, True
