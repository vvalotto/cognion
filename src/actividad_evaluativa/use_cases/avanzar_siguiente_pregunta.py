"""Caso de uso: el Docente avanza a la siguiente pregunta de la sesión en vivo (US-6.2.6, RF-09)."""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
)
from src.actividad_evaluativa.entities.errors import (
    ConcurrenciaOptimistaError,
    PreguntaActualNoCerrada,
    SesionNoExiste,
)
from src.actividad_evaluativa.entities.eventos_en_vivo import SiguientePreguntaPresentada
from src.actividad_evaluativa.entities.ports.canal_tiempo_real_port import CanalTiempoRealPort
from src.actividad_evaluativa.entities.ports.event_store_port import (
    EventoParaAlmacenar,
    EventStorePort,
)
from src.actividad_evaluativa.entities.ports.pregunta_consulta_port import PreguntaConsultaPort
from src.actividad_evaluativa.use_cases.pregunta_presentada import (
    mensaje_pregunta_presentada,
    payload_pregunta_presentada,
    tipo_de_pregunta,
)

AGGREGATE_TYPE_SESION = "ActividadEvaluativaEnVivo"


class AvanzarSiguientePreguntaUseCase:
    """Orquesta el avance: validación, persistencia y broadcast del nuevo enunciado."""

    def __init__(
        self,
        event_store: EventStorePort,
        pregunta_consulta: PreguntaConsultaPort,
        canal: CanalTiempoRealPort,
    ) -> None:
        """Recibe el event store, la consulta de preguntas de Banco y el canal en vivo."""
        self._event_store = event_store
        self._pregunta_consulta = pregunta_consulta
        self._canal = canal

    async def execute(self, sesion_id: UUID) -> ActividadEvaluativaEnVivo:
        """Avanza a la siguiente pregunta y publica su enunciado a todos los conectados.

        Levanta `SesionNoExiste`, `SesionNoEnCurso`, `PreguntaActualNoCerrada` o
        `NoQuedanPreguntas`. Dos avances concurrentes: el segundo choca con el chequeo optimista
        y se traduce a `PreguntaActualNoCerrada` (el primero ya dejó la pregunta nueva sin
        cerrar). Publica recién después de persistir; el canal es best-effort.
        """
        eventos = await self._event_store.load(AGGREGATE_TYPE_SESION, sesion_id)
        if not eventos:
            raise SesionNoExiste(sesion_id)

        sesion = ActividadEvaluativaEnVivo.reconstruir(eventos)
        sesion.avanzar()

        contenido = await self._pregunta_consulta.obtener_contenido(
            sesion.pregunta_actual().pregunta_id
        )
        evento = SiguientePreguntaPresentada.desde_sesion(
            sesion, contenido.texto, tipo_de_pregunta(contenido)
        )

        try:
            await self._event_store.append(
                AGGREGATE_TYPE_SESION,
                sesion_id,
                len(eventos),
                [
                    EventoParaAlmacenar(
                        event_type="SiguientePreguntaPresentada",
                        payload=payload_pregunta_presentada(evento),
                    )
                ],
            )
        except ConcurrenciaOptimistaError as exc:
            raise PreguntaActualNoCerrada(sesion_id) from exc

        await self._canal.publicar(sesion_id, mensaje_pregunta_presentada(evento))
        return sesion
