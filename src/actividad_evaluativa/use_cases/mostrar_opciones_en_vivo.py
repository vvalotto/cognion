"""Caso de uso: el Docente muestra las opciones de la pregunta actual (US-6.2.2, RF-09)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
)
from src.actividad_evaluativa.entities.errors import (
    ConcurrenciaOptimistaError,
    OpcionesYaMostradas,
    SesionNoExiste,
)
from src.actividad_evaluativa.entities.eventos_en_vivo import OpcionesEnVivoMostradas
from src.actividad_evaluativa.entities.ports.canal_tiempo_real_port import CanalTiempoRealPort
from src.actividad_evaluativa.entities.ports.event_store_port import (
    EventoParaAlmacenar,
    EventStorePort,
)
from src.actividad_evaluativa.entities.ports.pregunta_consulta_port import PreguntaConsultaPort

AGGREGATE_TYPE_SESION = "ActividadEvaluativaEnVivo"


def _payload(evento: OpcionesEnVivoMostradas) -> dict[str, Any]:
    """Arma el payload persistido de `OpcionesEnVivoMostradas` (sin la opción correcta)."""
    return {
        "sesion_id": str(evento.sesion_id),
        "pregunta_actual_indice": evento.pregunta_actual_indice,
        "pregunta_id": str(evento.pregunta_id),
        "opciones": evento.opciones,
        "ocurrido_en": evento.ocurrido_en.isoformat(),
    }


def _mensaje_opciones(
    evento: OpcionesEnVivoMostradas, tiempo_limite_segundos: int
) -> dict[str, Any]:
    """Arma el mensaje de broadcast de las opciones — arranca el temporizador (§16)."""
    return {
        "tipo": "opciones_mostradas",
        "pregunta_actual_indice": evento.pregunta_actual_indice,
        "opciones": evento.opciones,
        "tiempo_limite_por_pregunta_segundos": tiempo_limite_segundos,
        "cantidad_respuestas": 0,
    }


class MostrarOpcionesEnVivoUseCase:
    """Orquesta la revelación de opciones: validación, persistencia y broadcast."""

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
        """Muestra las opciones de la pregunta actual a todos los conectados.

        Levanta `SesionNoExiste`, `SesionNoEnCurso` u `OpcionesYaMostradas` (incluida la carrera
        de dos pedidos simultáneos, que el chequeo optimista del event store resuelve dejando
        ganar a uno). Publica recién después de persistir; el canal es best-effort.
        """
        eventos = await self._event_store.load(AGGREGATE_TYPE_SESION, sesion_id)
        if not eventos:
            raise SesionNoExiste(sesion_id)

        sesion = ActividadEvaluativaEnVivo.reconstruir(eventos)
        ahora = datetime.now(UTC)
        sesion.mostrar_opciones(ahora)

        contenido = await self._pregunta_consulta.obtener_contenido(
            sesion.pregunta_actual().pregunta_id
        )
        evento = OpcionesEnVivoMostradas.desde_sesion(sesion, contenido.opciones, ahora)

        try:
            await self._event_store.append(
                AGGREGATE_TYPE_SESION,
                sesion_id,
                len(eventos),
                [
                    EventoParaAlmacenar(
                        event_type="OpcionesEnVivoMostradas", payload=_payload(evento)
                    )
                ],
            )
        except ConcurrenciaOptimistaError as exc:
            raise OpcionesYaMostradas(sesion_id) from exc

        await self._canal.publicar(
            sesion_id, _mensaje_opciones(evento, sesion.tiempo_limite_por_pregunta_segundos)
        )
        return sesion
