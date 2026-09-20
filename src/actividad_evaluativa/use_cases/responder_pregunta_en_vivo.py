"""Caso de uso: un Estudiante responde la pregunta actual de una sesión en vivo (US-6.2.4, RF-09)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
)
from src.actividad_evaluativa.entities.errors import (
    ConcurrenciaOptimistaError,
    ParticipacionNoExiste,
    RespuestaYaRegistrada,
    SesionNoExiste,
)
from src.actividad_evaluativa.entities.eventos_en_vivo import RespuestaEnVivoRegistrada
from src.actividad_evaluativa.entities.participacion_en_vivo import ParticipacionEnVivo
from src.actividad_evaluativa.entities.ports.canal_tiempo_real_port import CanalTiempoRealPort
from src.actividad_evaluativa.entities.ports.event_store_port import (
    EventoParaAlmacenar,
    EventStorePort,
)
from src.actividad_evaluativa.entities.ports.pregunta_consulta_port import PreguntaConsultaPort
from src.actividad_evaluativa.entities.ports.proyecciones_en_vivo_port import (
    ProyeccionesEnVivoPort,
    ProyeccionesEnVivoQueryPort,
)
from src.actividad_evaluativa.entities.puntaje_en_vivo import calcular_puntaje

AGGREGATE_TYPE_SESION = "ActividadEvaluativaEnVivo"
AGGREGATE_TYPE_PARTICIPACION = "ParticipacionEnVivo"


@dataclass(frozen=True)
class ResultadoRespuestaEnVivo:
    """Feedback personal de la respuesta: acierto, puntos de la pregunta y acumulado (sin ranking)."""

    es_correcta: bool
    puntaje: int
    puntaje_acumulado: int


def _opcion_de(contenido: dict[str, Any]) -> str:
    """Clave de la opción para el histograma: índice (opción múltiple) o verdadero/falso."""
    if "opcion_indice" in contenido:
        return str(contenido["opcion_indice"])
    return "verdadero" if contenido.get("valor") else "falso"


def _payload(evento: RespuestaEnVivoRegistrada) -> dict[str, Any]:
    """Arma el payload persistido de `RespuestaEnVivoRegistrada`."""
    return {
        "sesion_id": str(evento.sesion_id),
        "estudiante_id": str(evento.estudiante_id),
        "pregunta_id": str(evento.pregunta_id),
        "contenido": evento.contenido,
        "es_correcta": evento.es_correcta,
        "tiempo_respuesta_segundos": evento.tiempo_respuesta_segundos,
        "puntaje": evento.puntaje,
        "ocurrido_en": evento.ocurrido_en.isoformat(),
    }


def _mensaje_conteo(pregunta_actual_indice: int | None, cantidad: int) -> dict[str, Any]:
    """Arma el broadcast del total de respuestas — sin desglose por opción (§16)."""
    return {
        "tipo": "conteo_respuestas_actualizado",
        "pregunta_actual_indice": pregunta_actual_indice,
        "cantidad_respuestas": cantidad,
    }


class ResponderPreguntaEnVivoUseCase:
    """Orquesta la respuesta: validación, corrección, puntaje, proyecciones y broadcast."""

    def __init__(
        self,
        event_store: EventStorePort,
        pregunta_consulta: PreguntaConsultaPort,
        proyecciones: ProyeccionesEnVivoPort,
        proyecciones_query: ProyeccionesEnVivoQueryPort,
        canal: CanalTiempoRealPort,
    ) -> None:
        """Recibe el event store, la consulta de preguntas, las proyecciones y el canal en vivo."""
        self._event_store = event_store
        self._pregunta_consulta = pregunta_consulta
        self._proyecciones = proyecciones
        self._proyecciones_query = proyecciones_query
        self._canal = canal

    async def execute(
        self,
        sesion_id: UUID,
        estudiante_id: UUID,
        pregunta_id: UUID,
        contenido: dict[str, Any],
    ) -> ResultadoRespuestaEnVivo:
        """Registra la respuesta del Estudiante y devuelve su feedback personal.

        Levanta `SesionNoExiste`, `ParticipacionNoExiste` y los rechazos de
        `validar_para_responder` (`SesionNoEnCurso`, `PreguntaNoActual`, `PreguntaYaCerrada`,
        `OpcionesNoMostradasTodavia`, `TiempoAgotado`) y `RespuestaYaRegistrada` (INV-AEV-07,
        incluido el doble envío concurrente, que resuelve el chequeo optimista del stream).
        Proyecciones y evento se confirman juntos; el broadcast va después y es best-effort.
        """
        eventos_sesion = await self._event_store.load(AGGREGATE_TYPE_SESION, sesion_id)
        if not eventos_sesion:
            raise SesionNoExiste(sesion_id)
        participacion_id = ParticipacionEnVivo.id_para(sesion_id, estudiante_id)
        eventos = await self._event_store.load(AGGREGATE_TYPE_PARTICIPACION, participacion_id)
        if not eventos:
            raise ParticipacionNoExiste(sesion_id, estudiante_id)

        sesion = ActividadEvaluativaEnVivo.reconstruir(eventos_sesion)
        participacion = ParticipacionEnVivo.reconstruir(eventos)
        tiempo = sesion.validar_para_responder(pregunta_id, datetime.now(UTC))
        participacion.validar_para_responder(pregunta_id)

        es_correcta = await self._pregunta_consulta.evaluar_correccion(pregunta_id, contenido)
        niveles = await self._pregunta_consulta.obtener_niveles(pregunta_id)
        puntaje = calcular_puntaje(
            es_correcta,
            tiempo,
            sesion.tiempo_limite_por_pregunta_segundos,
            niveles.dificultad,
            niveles.importancia,
        )
        respuesta = participacion.responder(pregunta_id, contenido, es_correcta, tiempo, puntaje)
        evento = RespuestaEnVivoRegistrada.desde_respuesta(participacion, respuesta)

        await self._persistir(sesion_id, estudiante_id, participacion, eventos, evento)
        cantidad = await self._proyecciones_query.cantidad_respuestas(sesion_id, pregunta_id)
        await self._canal.publicar(
            sesion_id, _mensaje_conteo(sesion.pregunta_actual_indice, cantidad)
        )
        return ResultadoRespuestaEnVivo(es_correcta, puntaje, participacion.puntaje_acumulado)

    async def _persistir(
        self,
        sesion_id: UUID,
        estudiante_id: UUID,
        participacion: ParticipacionEnVivo,
        eventos_previos: list[Any],
        evento: RespuestaEnVivoRegistrada,
    ) -> None:
        """Escribe la proyección (sin commit) y el evento; el `append` confirma ambos juntos."""
        await self._proyecciones.registrar_respuesta(
            sesion_id,
            estudiante_id,
            evento.pregunta_id,
            _opcion_de(evento.contenido),
            evento.puntaje,
        )
        try:
            await self._event_store.append(
                AGGREGATE_TYPE_PARTICIPACION,
                participacion.id,
                len(eventos_previos),
                [
                    EventoParaAlmacenar(
                        event_type="RespuestaEnVivoRegistrada", payload=_payload(evento)
                    )
                ],
            )
        except ConcurrenciaOptimistaError as exc:
            await self._proyecciones.descartar_pendientes()
            raise RespuestaYaRegistrada(sesion_id, evento.pregunta_id) from exc
