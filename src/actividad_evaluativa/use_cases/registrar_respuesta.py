"""Caso de uso: confirmación de una respuesta con persistencia atómica (US-3.2.1, RF-13)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from src.actividad_evaluativa.entities.actividad_evaluativa_periodo_abierto import (
    ActividadEvaluativaPeriodoAbierto,
)
from src.actividad_evaluativa.entities.errors import EvaluacionNoExiste, FueraDePeriodo
from src.actividad_evaluativa.entities.evaluacion import Evaluacion, Respuesta
from src.actividad_evaluativa.entities.eventos import RespuestaRegistrada
from src.actividad_evaluativa.entities.ports.event_store_port import (
    EventoParaAlmacenar,
    EventStorePort,
)
from src.actividad_evaluativa.entities.ports.pregunta_consulta_port import PreguntaConsultaPort

AGGREGATE_TYPE_ACTIVIDAD = "ActividadEvaluativaPeriodoAbierto"
AGGREGATE_TYPE_EVALUACION = "Evaluacion"


class RegistrarRespuestaUseCase:
    """Orquesta la confirmación atómica de una `Respuesta` sobre una `Evaluacion` `EnCurso`."""

    def __init__(
        self,
        pregunta_consulta: PreguntaConsultaPort,
        event_store: EventStorePort,
    ) -> None:
        """Recibe el puerto de consulta a Banco de Preguntas y el event store."""
        self._pregunta_consulta = pregunta_consulta
        self._event_store = event_store

    async def execute(
        self,
        evaluacion_id: UUID,
        estudiante_id: UUID,
        pregunta_id: UUID,
        contenido: dict[str, Any],
    ) -> Respuesta:
        """Registra la respuesta, o levanta el error de dominio correspondiente.

        Levanta `EvaluacionNoExiste` si `evaluacion_id` no tiene stream o no pertenece al
        estudiante autenticado, `FueraDePeriodo` si la actividad ya no está vigente,
        `PreguntaNoAsignada`/`IntentosAgotados`/`EvaluacionSuspendida`/`EvaluacionYaFinalizada`
        según INV-AE-07/08/12 (`Evaluacion.registrar_respuesta`).
        """
        eventos_evaluacion = await self._event_store.load(AGGREGATE_TYPE_EVALUACION, evaluacion_id)
        if not eventos_evaluacion:
            raise EvaluacionNoExiste(evaluacion_id)

        evaluacion = Evaluacion.reconstruir(eventos_evaluacion)
        if evaluacion.estudiante_id != estudiante_id:
            raise EvaluacionNoExiste(evaluacion_id)

        eventos_actividad = await self._event_store.load(
            AGGREGATE_TYPE_ACTIVIDAD, evaluacion.actividad_id
        )
        actividad = ActividadEvaluativaPeriodoAbierto.reconstruir(eventos_actividad)
        fecha_apertura = actividad.fecha_apertura
        fecha_cierre = actividad.fecha_cierre
        cantidad_intentos_permitidos = actividad.cantidad_intentos_permitidos

        ahora = datetime.now(UTC)
        if ahora < fecha_apertura or ahora > fecha_cierre:
            raise FueraDePeriodo(evaluacion.actividad_id, ahora)

        numero_intento = evaluacion.validar_para_registrar_respuesta(
            pregunta_id, cantidad_intentos_permitidos
        )
        es_correcta = await self._pregunta_consulta.evaluar_correccion(pregunta_id, contenido)
        respuesta = Respuesta(
            id=uuid4(),
            pregunta_id=pregunta_id,
            numero_intento=numero_intento,
            contenido=contenido,
            es_correcta=es_correcta,
        )

        evento = RespuestaRegistrada(
            respuesta_id=respuesta.id,
            evaluacion_id=evaluacion_id,
            pregunta_id=respuesta.pregunta_id,
            numero_intento=respuesta.numero_intento,
            contenido=respuesta.contenido,
            es_correcta=respuesta.es_correcta,
        )
        payload = {
            "respuesta_id": str(evento.respuesta_id),
            "evaluacion_id": str(evento.evaluacion_id),
            "pregunta_id": str(evento.pregunta_id),
            "numero_intento": evento.numero_intento,
            "contenido": evento.contenido,
            "es_correcta": evento.es_correcta,
            "ocurrido_en": evento.ocurrido_en.isoformat(),
        }
        await self._event_store.append(
            AGGREGATE_TYPE_EVALUACION,
            evaluacion_id,
            len(eventos_evaluacion),
            [EventoParaAlmacenar(event_type="RespuestaRegistrada", payload=payload)],
        )

        return respuesta
