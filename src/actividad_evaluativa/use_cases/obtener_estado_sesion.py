"""Caso de uso: consultar el estado actual de la sesión en vivo (US-6.2.8, reconexión)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
)
from src.actividad_evaluativa.entities.errors import SesionNoExiste
from src.actividad_evaluativa.entities.participacion_en_vivo import ParticipacionEnVivo
from src.actividad_evaluativa.entities.ports.event_store_port import EventStorePort
from src.actividad_evaluativa.entities.ports.pregunta_consulta_port import PreguntaConsultaPort
from src.actividad_evaluativa.use_cases.pregunta_presentada import tipo_de_pregunta

AGGREGATE_TYPE_SESION = "ActividadEvaluativaEnVivo"
AGGREGATE_TYPE_PARTICIPACION = "ParticipacionEnVivo"


@dataclass(frozen=True)
class PreguntaActualVista:
    """La pregunta actual tal como puede verla un cliente según el estado de la sesión."""

    pregunta_id: UUID
    enunciado: str
    tipo: str
    opciones: list[str] | None
    """Solo con las opciones ya mostradas; `None` también para Verdadero/Falso."""
    respuesta_correcta: dict[str, Any] | None
    """Solo con la pregunta ya cerrada: `{contenido, texto, opciones}`."""


@dataclass(frozen=True)
class EstadoSesion:
    """Estado consultable de una sesión en vivo; los campos del Estudiante son `None` al Docente."""

    sesion: ActividadEvaluativaEnVivo
    pregunta_actual: PreguntaActualVista | None
    ya_respondio: bool | None
    puntaje_acumulado: int | None

    @property
    def opciones_mostradas_en(self) -> datetime | None:
        """Instante en que se mostraron las opciones, base del tiempo restante del cliente."""
        return self.sesion.opciones_mostradas_en


async def _pregunta_actual(
    sesion: ActividadEvaluativaEnVivo, pregunta_consulta: PreguntaConsultaPort
) -> PreguntaActualVista | None:
    """Arma la pregunta actual sin exponer nunca la correcta antes de cerrarla."""
    if sesion.pregunta_actual_indice is None:
        return None
    pregunta_id = sesion.pregunta_actual().pregunta_id
    contenido = await pregunta_consulta.obtener_contenido(pregunta_id)
    correcta = None
    if sesion.pregunta_actual_cerrada:
        detalle = await pregunta_consulta.obtener_detalle_correccion(pregunta_id)
        correcta = {
            "contenido": detalle.contenido_correcto,
            "texto": detalle.texto,
            "opciones": detalle.opciones,
        }
    return PreguntaActualVista(
        pregunta_id=pregunta_id,
        enunciado=contenido.texto,
        tipo=tipo_de_pregunta(contenido),
        opciones=contenido.opciones if sesion.opciones_mostradas else None,
        respuesta_correcta=correcta,
    )


async def _avance_del_estudiante(
    event_store: EventStorePort,
    sesion: ActividadEvaluativaEnVivo,
    estudiante_id: UUID,
) -> tuple[bool, int]:
    """Devuelve `(ya_respondio, puntaje_acumulado)`; sin participación: `(False, 0)`."""
    participacion_id = ParticipacionEnVivo.id_para(sesion.id, estudiante_id)
    eventos = await event_store.load(AGGREGATE_TYPE_PARTICIPACION, participacion_id)
    if not eventos:
        return False, 0
    participacion = ParticipacionEnVivo.reconstruir(eventos)
    actual = (
        sesion.pregunta_actual().pregunta_id if sesion.pregunta_actual_indice is not None else None
    )
    ya_respondio = any(r.pregunta_id == actual for r in participacion.respuestas)
    return ya_respondio, participacion.puntaje_acumulado


class ObtenerEstadoSesionUseCase:
    """Reconstruye el estado de la sesión para que un cliente se ponga al día por HTTP."""

    def __init__(
        self, event_store: EventStorePort, pregunta_consulta: PreguntaConsultaPort
    ) -> None:
        """Recibe el event store y la consulta de preguntas de Banco."""
        self._event_store = event_store
        self._pregunta_consulta = pregunta_consulta

    async def execute(self, sesion_id: UUID, estudiante_id: UUID | None = None) -> EstadoSesion:
        """Devuelve el estado; con `estudiante_id` suma su avance propio. No escribe nada.

        Levanta `SesionNoExiste`. Nunca expone las opciones antes de mostrarlas ni la respuesta
        correcta antes de cerrar la pregunta.
        """
        eventos = await self._event_store.load(AGGREGATE_TYPE_SESION, sesion_id)
        if not eventos:
            raise SesionNoExiste(sesion_id)

        sesion = ActividadEvaluativaEnVivo.reconstruir(eventos)
        pregunta = await _pregunta_actual(sesion, self._pregunta_consulta)
        if estudiante_id is None:
            return EstadoSesion(sesion, pregunta, None, None)
        ya_respondio, puntaje = await _avance_del_estudiante(
            self._event_store, sesion, estudiante_id
        )
        return EstadoSesion(sesion, pregunta, ya_respondio, puntaje)
