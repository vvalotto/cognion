"""Caso de uso: query de revisión completa de una `Evaluacion` `Finalizada` (US-3.2.3, RF-13)."""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.entities.errors import EvaluacionNoExiste, EvaluacionNoFinalizada
from src.actividad_evaluativa.entities.evaluacion import (
    EstadoEvaluacion,
    Evaluacion,
    PreguntaAsignada,
)
from src.actividad_evaluativa.entities.ports.event_store_port import EventStorePort
from src.actividad_evaluativa.entities.ports.pregunta_consulta_port import PreguntaConsultaPort
from src.actividad_evaluativa.entities.revision_evaluacion import (
    DetallePreguntaRevision,
    RevisionEvaluacion,
)

AGGREGATE_TYPE_EVALUACION = "Evaluacion"


class ObtenerRevisionEvaluacionUseCase:
    """Compone el detalle por pregunta y el resumen de una `Evaluacion` ya `Finalizada`.

    Query pura — no muta `Evaluacion` ni emite eventos (`BC-actividad-evaluativa-modelo.md`
    §4). Vive separado de los comandos sobre `Evaluacion` (`EvaluacionesController`) en su
    propio `RevisionController` para no repetir el CRITICAL de CBO ya visto en Incremento 2 al
    mezclar comandos y queries en un mismo controller.
    """

    def __init__(
        self,
        pregunta_consulta: PreguntaConsultaPort,
        event_store: EventStorePort,
    ) -> None:
        """Recibe el puerto de consulta a Banco de Preguntas y el event store."""
        self._pregunta_consulta = pregunta_consulta
        self._event_store = event_store

    async def execute(self, evaluacion_id: UUID, estudiante_id: UUID) -> RevisionEvaluacion:
        """Arma la revisión, o levanta el error de dominio correspondiente.

        Levanta `EvaluacionNoExiste` si `evaluacion_id` no tiene stream o no pertenece al
        estudiante autenticado, `EvaluacionNoFinalizada` si `Evaluacion.estado` no es
        `Finalizada` (RF-13: nunca antes de finalizar).
        """
        eventos = await self._event_store.load(AGGREGATE_TYPE_EVALUACION, evaluacion_id)
        if not eventos:
            raise EvaluacionNoExiste(evaluacion_id)

        evaluacion = Evaluacion.reconstruir(eventos)
        if evaluacion.estudiante_id != estudiante_id:
            raise EvaluacionNoExiste(evaluacion_id)

        if evaluacion.estado is not EstadoEvaluacion.FINALIZADA:
            raise EvaluacionNoFinalizada(evaluacion_id)

        detalle = [
            await self._detalle_de(evaluacion, pregunta_asignada)
            for pregunta_asignada in evaluacion.preguntas_asignadas
        ]
        cantidad_correctas = sum(1 for fila in detalle if fila.es_correcta)

        return RevisionEvaluacion(
            evaluacion_id=evaluacion_id,
            cantidad_preguntas=len(detalle),
            cantidad_correctas=cantidad_correctas,
            cantidad_incorrectas=len(detalle) - cantidad_correctas,
            detalle=detalle,
        )

    async def _detalle_de(
        self, evaluacion: Evaluacion, pregunta_asignada: PreguntaAsignada
    ) -> DetallePreguntaRevision:
        """Arma el detalle de una `PreguntaAsignada` — respuesta vigente + corrección si falló.

        Una pregunta sin `Respuesta` cuenta como incorrecta (`es_correcta=False`) y siempre
        expone la respuesta correcta, mismo tratamiento que una respondida mal (decisión de
        diseño de `US-3.2.3`, ver spec).
        """
        respuesta = evaluacion.respuesta_vigente_de(pregunta_asignada.pregunta_id)
        detalle_correccion = await self._pregunta_consulta.obtener_detalle_correccion(
            pregunta_asignada.pregunta_id
        )
        es_correcta = respuesta is not None and respuesta.es_correcta

        return DetallePreguntaRevision(
            pregunta_id=pregunta_asignada.pregunta_id,
            orden=pregunta_asignada.orden,
            texto=detalle_correccion.texto,
            respondida=respuesta is not None,
            contenido_propio=respuesta.contenido if respuesta is not None else None,
            es_correcta=es_correcta,
            contenido_correcto=(None if es_correcta else detalle_correccion.contenido_correcto),
        )
