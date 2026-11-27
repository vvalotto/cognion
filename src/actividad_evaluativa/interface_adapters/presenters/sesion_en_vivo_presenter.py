"""Presenters del modo en vivo (`ADR-031`): entidades y resultados -> salidas de la API.

Los `dataclass` de salida tienen los mismos campos que los esquemas de `frameworks/api/schemas.py`;
FastAPI los valida contra el `response_model` sin código extra. Sin Pydantic ni FastAPI.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import ActividadEvaluativaEnVivo
from src.actividad_evaluativa.entities.participacion_en_vivo import ParticipacionEnVivo
from src.actividad_evaluativa.entities.ports.participantes_sesion_query_port import (
    ParticipanteResumen,
)
from src.actividad_evaluativa.entities.ports.proyecciones_en_vivo_port import ParticipanteEnRanking
from src.actividad_evaluativa.entities.ports.sesiones_en_vivo_query_port import SesionEnVivoResumen
from src.actividad_evaluativa.use_cases.obtener_estado_sesion import EstadoSesion, ResultadoPregunta
from src.actividad_evaluativa.use_cases.responder_pregunta_en_vivo import ResultadoRespuestaEnVivo


@dataclass(frozen=True)
class SesionEnVivoSalida:
    """Una sesión en vivo."""

    id: UUID
    comision_id: UUID
    materia_id: UUID
    unidad_tematica: str | None
    tema: str | None
    cantidad_preguntas: int
    tiempo_limite_por_pregunta_segundos: int
    estado: str
    pregunta_actual_indice: int | None = None


@dataclass(frozen=True)
class ParticipacionEnVivoSalida:
    """La participación de un Estudiante en una sesión."""

    sesion_id: UUID
    estudiante_id: UUID
    unido_en: datetime


@dataclass(frozen=True)
class RespuestaEnVivoSalida:
    """El resultado de responder una pregunta en vivo."""

    es_correcta: bool
    puntaje: int
    puntaje_acumulado: int


@dataclass(frozen=True)
class RespuestaCorrectaSalida:
    """La respuesta correcta de la pregunta actual, una vez cerrada."""

    contenido: dict[str, Any]
    texto: str
    opciones: list[str] | None


@dataclass(frozen=True)
class PreguntaActualSalida:
    """La pregunta actual de una sesión."""

    pregunta_id: UUID
    enunciado: str
    tipo: str
    opciones: list[str] | None = None
    respuesta_correcta: RespuestaCorrectaSalida | None = None


@dataclass(frozen=True)
class OpcionDistribuidaSalida:
    """La cantidad de respuestas de una opción."""

    opcion: str
    cantidad: int


@dataclass(frozen=True)
class RankingItemSalida:
    """Una fila del ranking de una sesión."""

    posicion: int
    estudiante_id: UUID
    puntaje_acumulado: int
    nombre: str


@dataclass(frozen=True)
class ResultadoPreguntaSalida:
    """El resultado de una pregunta cerrada: distribución y ranking."""

    distribucion: list[OpcionDistribuidaSalida]
    ranking: list[RankingItemSalida]


@dataclass(frozen=True)
class EstadoSesionEnVivoSalida:
    """El estado completo de una sesión en vivo."""

    estado: str
    comision_id: UUID
    cantidad_preguntas: int
    tiempo_limite_por_pregunta_segundos: int
    pregunta_actual_indice: int | None
    opciones_mostradas: bool
    opciones_mostradas_en: datetime | None
    pregunta_actual_cerrada: bool
    pregunta_actual: PreguntaActualSalida | None
    ya_respondio: bool | None = None
    puntaje_acumulado: int | None = None
    total_participantes: int = 0
    cantidad_respuestas: int = 0
    resultado_pregunta: ResultadoPreguntaSalida | None = None


@dataclass(frozen=True)
class ParticipanteSalida:
    """Un participante de una sesión."""

    estudiante_id: UUID
    unido_en: datetime
    nombre: str


@dataclass(frozen=True)
class SesionEnVivoResumenSalida:
    """Una sesión en el listado."""

    id: UUID
    comision_id: UUID
    materia_id: UUID
    materia_nombre: str
    cantidad_preguntas: int
    tiempo_limite_por_pregunta_segundos: int
    estado: str
    unidad_tematica: str | None
    tema: str | None
    creada_en: datetime


def presentar_sesion(sesion: ActividadEvaluativaEnVivo) -> SesionEnVivoSalida:
    """Arma la salida de una sesión en vivo."""
    return SesionEnVivoSalida(
        id=sesion.id,
        comision_id=sesion.comision_id,
        materia_id=sesion.materia_id,
        unidad_tematica=sesion.unidad_tematica,
        tema=sesion.tema,
        cantidad_preguntas=len(sesion.preguntas),
        tiempo_limite_por_pregunta_segundos=sesion.tiempo_limite_por_pregunta_segundos,
        estado=sesion.estado.value,
        pregunta_actual_indice=sesion.pregunta_actual_indice,
    )


def presentar_participacion(participacion: ParticipacionEnVivo) -> ParticipacionEnVivoSalida:
    """Arma la salida de una participación."""
    return ParticipacionEnVivoSalida(
        sesion_id=participacion.sesion_id,
        estudiante_id=participacion.estudiante_id,
        unido_en=participacion.unido_en,
    )


def presentar_respuesta_en_vivo(resultado: ResultadoRespuestaEnVivo) -> RespuestaEnVivoSalida:
    """Arma la salida del resultado de una respuesta en vivo."""
    return RespuestaEnVivoSalida(
        es_correcta=resultado.es_correcta,
        puntaje=resultado.puntaje,
        puntaje_acumulado=resultado.puntaje_acumulado,
    )


def presentar_ranking(ranking: list[ParticipanteEnRanking]) -> list[RankingItemSalida]:
    """Arma las filas del ranking."""
    return [
        RankingItemSalida(
            posicion=r.posicion,
            estudiante_id=r.estudiante_id,
            puntaje_acumulado=r.puntaje_acumulado,
            nombre=r.nombre,
        )
        for r in ranking
    ]


def _presentar_resultado_pregunta(
    resultado: ResultadoPregunta | None,
) -> ResultadoPreguntaSalida | None:
    """`None` sin resultado todavía (`US-6.3.3`)."""
    if resultado is None:
        return None
    return ResultadoPreguntaSalida(
        distribucion=[
            OpcionDistribuidaSalida(opcion=d.opcion, cantidad=d.cantidad)
            for d in resultado.distribucion
        ],
        ranking=presentar_ranking(resultado.ranking),
    )


def presentar_estado_sesion(estado: EstadoSesion) -> EstadoSesionEnVivoSalida:
    """Arma el estado de una sesión a partir del estado consultado (`US-6.2.8`)."""
    sesion = estado.sesion
    pregunta = estado.pregunta_actual
    return EstadoSesionEnVivoSalida(
        estado=sesion.estado.value,
        comision_id=sesion.comision_id,
        cantidad_preguntas=len(sesion.preguntas),
        tiempo_limite_por_pregunta_segundos=sesion.tiempo_limite_por_pregunta_segundos,
        pregunta_actual_indice=sesion.pregunta_actual_indice,
        opciones_mostradas=sesion.opciones_mostradas,
        opciones_mostradas_en=sesion.opciones_mostradas_en,
        pregunta_actual_cerrada=sesion.pregunta_actual_cerrada,
        pregunta_actual=(
            None
            if pregunta is None
            else PreguntaActualSalida(
                pregunta_id=pregunta.pregunta_id,
                enunciado=pregunta.enunciado,
                tipo=pregunta.tipo,
                opciones=pregunta.opciones,
                respuesta_correcta=(
                    None
                    if pregunta.respuesta_correcta is None
                    else RespuestaCorrectaSalida(**pregunta.respuesta_correcta)
                ),
            )
        ),
        ya_respondio=estado.ya_respondio,
        puntaje_acumulado=estado.puntaje_acumulado,
        total_participantes=estado.total_participantes,
        cantidad_respuestas=estado.cantidad_respuestas,
        resultado_pregunta=_presentar_resultado_pregunta(estado.resultado_pregunta),
    )


def presentar_participantes(participantes: list[ParticipanteResumen]) -> list[ParticipanteSalida]:
    """Arma el listado de participantes de una sesión."""
    return [
        ParticipanteSalida(estudiante_id=p.estudiante_id, unido_en=p.unido_en, nombre=p.nombre)
        for p in participantes
    ]


def presentar_sesiones_resumen(
    sesiones: list[SesionEnVivoResumen],
) -> list[SesionEnVivoResumenSalida]:
    """Arma el listado de sesiones en vivo."""
    return [
        SesionEnVivoResumenSalida(
            id=s.id,
            comision_id=s.comision_id,
            materia_id=s.materia_id,
            materia_nombre=s.materia_nombre,
            cantidad_preguntas=s.cantidad_preguntas,
            tiempo_limite_por_pregunta_segundos=s.tiempo_limite_por_pregunta_segundos,
            estado=s.estado.value,
            unidad_tematica=s.unidad_tematica,
            tema=s.tema,
            creada_en=s.creada_en,
        )
        for s in sesiones
    ]
