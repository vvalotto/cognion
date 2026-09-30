"""Caso de uso: consultar el estado actual de la sesión en vivo (US-6.2.8, reconexión)."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any
from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
)
from src.actividad_evaluativa.entities.errors import SesionNoExiste
from src.actividad_evaluativa.entities.participacion_en_vivo import ParticipacionEnVivo
from src.actividad_evaluativa.entities.ports.estudiante_consulta_port import (
    EstudianteConsultaPort,
)
from src.actividad_evaluativa.entities.ports.event_store_port import EventStorePort
from src.actividad_evaluativa.entities.ports.participantes_sesion_query_port import (
    ParticipantesSesionQueryPort,
)
from src.actividad_evaluativa.entities.ports.pregunta_consulta_port import PreguntaConsultaPort
from src.actividad_evaluativa.entities.ports.proyecciones_en_vivo_port import (
    OpcionDistribuida,
    ParticipanteEnRanking,
    ProyeccionesEnVivoQueryPort,
)
from src.actividad_evaluativa.use_cases._resolucion_nombres import resolver_nombres
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
class ResultadoPregunta:
    """Histograma y ranking de la pregunta ya cerrada — mismo contenido que `pregunta_cerrada`."""

    distribucion: list[OpcionDistribuida]
    ranking: list[ParticipanteEnRanking]


@dataclass(frozen=True)
class EstadoSesion:
    """Estado consultable de una sesión en vivo; los campos del Estudiante son `None` al Docente."""

    sesion: ActividadEvaluativaEnVivo
    pregunta_actual: PreguntaActualVista | None
    ya_respondio: bool | None
    puntaje_acumulado: int | None
    total_participantes: int
    cantidad_respuestas: int
    resultado_pregunta: ResultadoPregunta | None
    """Solo para el Docente, y solo con la pregunta actual cerrada (`US-6.3.3`)."""

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


async def _cantidad_respuestas(
    sesion: ActividadEvaluativaEnVivo, proyecciones: ProyeccionesEnVivoQueryPort
) -> int:
    """Respuestas registradas a la pregunta actual; `0` sin pregunta actual (`US-6.3.3`)."""
    if sesion.pregunta_actual_indice is None:
        return 0
    pregunta_id = sesion.pregunta_actual().pregunta_id
    return await proyecciones.cantidad_respuestas(sesion.id, pregunta_id)


async def _resultado_pregunta(
    sesion: ActividadEvaluativaEnVivo,
    proyecciones: ProyeccionesEnVivoQueryPort,
    estudiante_consulta: EstudianteConsultaPort,
) -> ResultadoPregunta | None:
    """Histograma + ranking de la pregunta actual, solo si ya está cerrada (`US-6.3.3`).

    `None` sin pregunta actual o con la pregunta todavía abierta — mismo contenido que el
    broadcast `pregunta_cerrada`, incluido el `nombre` de cada fila del ranking (`US-6.3.1`).
    """
    if sesion.pregunta_actual_indice is None or not sesion.pregunta_actual_cerrada:
        return None
    pregunta_id = sesion.pregunta_actual().pregunta_id
    distribucion = await proyecciones.distribucion(sesion.id, pregunta_id)
    ranking = await proyecciones.ranking(sesion.id)
    nombres = await resolver_nombres(estudiante_consulta, (r.estudiante_id for r in ranking))
    ranking_con_nombre = [replace(r, nombre=nombres[r.estudiante_id]) for r in ranking]
    return ResultadoPregunta(distribucion=distribucion, ranking=ranking_con_nombre)


class ObtenerEstadoSesionUseCase:
    """Reconstruye el estado de la sesión para que un cliente se ponga al día por HTTP."""

    def __init__(
        self,
        event_store: EventStorePort,
        pregunta_consulta: PreguntaConsultaPort,
        proyecciones: ProyeccionesEnVivoQueryPort,
        participantes: ParticipantesSesionQueryPort,
        estudiante_consulta: EstudianteConsultaPort,
    ) -> None:
        """Recibe event store y las consultas de Banco, proyecciones, participantes, Identidad."""
        self._event_store = event_store
        self._pregunta_consulta = pregunta_consulta
        self._proyecciones = proyecciones
        self._participantes = participantes
        self._estudiante_consulta = estudiante_consulta

    async def execute(self, sesion_id: UUID, estudiante_id: UUID | None = None) -> EstadoSesion:
        """Devuelve el estado; con `estudiante_id` suma su avance propio. No escribe nada.

        Levanta `SesionNoExiste`. Nunca expone las opciones antes de mostrarlas ni la respuesta
        correcta antes de cerrar la pregunta. `resultado_pregunta` (histograma + ranking) solo
        se arma para el Docente (`estudiante_id is None`) — el Estudiante nunca ve el ranking
        antes del resultado final.
        """
        eventos = await self._event_store.load(AGGREGATE_TYPE_SESION, sesion_id)
        if not eventos:
            raise SesionNoExiste(sesion_id)

        sesion = ActividadEvaluativaEnVivo.reconstruir(eventos)
        pregunta = await _pregunta_actual(sesion, self._pregunta_consulta)
        total_participantes = len(await self._participantes.listar(sesion_id))
        cantidad_respuestas = await _cantidad_respuestas(sesion, self._proyecciones)

        if estudiante_id is None:
            resultado = await _resultado_pregunta(
                sesion, self._proyecciones, self._estudiante_consulta
            )
            return EstadoSesion(
                sesion, pregunta, None, None, total_participantes, cantidad_respuestas, resultado
            )
        ya_respondio, puntaje = await _avance_del_estudiante(
            self._event_store, sesion, estudiante_id
        )
        return EstadoSesion(
            sesion,
            pregunta,
            ya_respondio,
            puntaje,
            total_participantes,
            cantidad_respuestas,
            None,
        )
