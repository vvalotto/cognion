"""Presenters de Analytics (`ADR-031`): resultado de los casos de uso -> tipos de salida de la API.

Los `dataclass` de salida tienen los mismos campos que los esquemas de `frameworks/api/schemas.py`;
FastAPI los valida contra el `response_model` sin código extra. Sin Pydantic ni FastAPI: el armado
se prueba solo.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.analytics.use_cases.obtener_completitud_por_actividad import CompletitudPorActividad
from src.analytics.use_cases.obtener_desempeno_estudiante import DesempenoEstudiante
from src.analytics.use_cases.obtener_desempeno_por_comision import DesempenoComisionFila
from src.analytics.use_cases.obtener_evolucion_temporal_comision import (
    EvolucionTemporalComisionPunto,
)
from src.analytics.use_cases.obtener_evolucion_temporal_estudiante import EvolucionTemporalPunto
from src.analytics.use_cases.obtener_ranking_preguntas_falladas import RankingPreguntaFallada
from src.analytics.use_cases.obtener_tasa_error_por_tema import TasaErrorTema


@dataclass(frozen=True)
class EvaluacionDetalleSalida:
    """Fila de detalle de una evaluación finalizada del Estudiante."""

    evaluacion_id: UUID
    actividad_id: UUID
    finalizada_en: datetime
    cantidad_correctas: int
    cantidad_incorrectas: int


@dataclass(frozen=True)
class ResumenDesempenoSalida:
    """Acumulado sobre todas las evaluaciones finalizadas del detalle."""

    total_correctas: int
    total_incorrectas: int
    porcentaje_acierto: int
    cantidad_evaluaciones: int


@dataclass(frozen=True)
class SesionEnVivoDetalleSalida:
    """Fila de detalle de una sesión en vivo finalizada en la que participó el Estudiante."""

    sesion_id: UUID
    comision_horario: str
    finalizada_en: datetime
    cantidad_preguntas: int
    cantidad_correctas: int
    cantidad_incorrectas: int
    puntaje_final: int
    posicion: int
    total_participantes: int


@dataclass(frozen=True)
class DesempenoEstudianteSalida:
    """Desempeño completo de un Estudiante en una materia."""

    evaluaciones: list[EvaluacionDetalleSalida]
    resumen: ResumenDesempenoSalida
    sesiones_en_vivo: list[SesionEnVivoDetalleSalida]


@dataclass(frozen=True)
class TasaErrorTemaSalida:
    """Fila de la tasa de error por unidad y tema."""

    unidad_tematica: str
    tema: str
    cantidad_respuestas: int
    cantidad_incorrectas: int
    tasa_error: float


@dataclass(frozen=True)
class DesempenoComisionFilaSalida:
    """Fila del desempeño de un estudiante dentro de una comisión."""

    estudiante_id: UUID
    nombre: str
    porcentaje_aciertos_acumulado: float | None
    actividades_pendientes: int


@dataclass(frozen=True)
class EvolucionTemporalPuntoSalida:
    """Punto de la serie individual de evolución temporal."""

    actividad_id: UUID
    titulo_actividad: str
    finalizada_en: datetime
    porcentaje_acierto: int


@dataclass(frozen=True)
class EvolucionTemporalComisionPuntoSalida:
    """Punto de la serie de evolución temporal de una comisión."""

    actividad_id: UUID
    titulo_actividad: str
    porcentaje_aciertos_promedio: float


@dataclass(frozen=True)
class RankingPreguntaFalladaSalida:
    """Fila del ranking de preguntas más falladas."""

    pregunta_id: UUID
    enunciado: str
    unidad_tematica: str
    tema: str
    cantidad_presentaciones: int
    cantidad_fallos: int
    tasa_error: float


@dataclass(frozen=True)
class CompletitudFilaSalida:
    """Un estudiante del roster y el estado de su evaluación."""

    estudiante_id: UUID
    nombre: str
    estado: str


@dataclass(frozen=True)
class CompletitudResumenSalida:
    """Conteo agregado por estado de la completitud de una actividad."""

    finalizadas: int
    en_curso: int
    suspendidas: int
    sin_iniciar: int


@dataclass(frozen=True)
class CompletitudPorActividadSalida:
    """Completitud del roster aplicable de una actividad."""

    detalle: list[CompletitudFilaSalida]
    resumen: CompletitudResumenSalida


def presentar_desempeno_estudiante(desempeno: DesempenoEstudiante) -> DesempenoEstudianteSalida:
    """Arma la salida del desempeño de un Estudiante."""
    return DesempenoEstudianteSalida(
        evaluaciones=[
            EvaluacionDetalleSalida(
                evaluacion_id=e.evaluacion_id,
                actividad_id=e.actividad_id,
                finalizada_en=e.finalizada_en,
                cantidad_correctas=e.cantidad_correctas,
                cantidad_incorrectas=e.cantidad_incorrectas,
            )
            for e in desempeno.evaluaciones
        ],
        resumen=ResumenDesempenoSalida(
            total_correctas=desempeno.resumen.total_correctas,
            total_incorrectas=desempeno.resumen.total_incorrectas,
            porcentaje_acierto=desempeno.resumen.porcentaje_acierto,
            cantidad_evaluaciones=desempeno.resumen.cantidad_evaluaciones,
        ),
        sesiones_en_vivo=[
            SesionEnVivoDetalleSalida(
                sesion_id=s.sesion_id,
                comision_horario=s.comision_horario,
                finalizada_en=s.finalizada_en,
                cantidad_preguntas=s.cantidad_preguntas,
                cantidad_correctas=s.cantidad_correctas,
                cantidad_incorrectas=s.cantidad_incorrectas,
                puntaje_final=s.puntaje_final,
                posicion=s.posicion,
                total_participantes=s.total_participantes,
            )
            for s in desempeno.sesiones_en_vivo
        ],
    )


def presentar_tasas_error(tasas: list[TasaErrorTema]) -> list[TasaErrorTemaSalida]:
    """Arma las filas de la tasa de error por tema."""
    return [
        TasaErrorTemaSalida(
            unidad_tematica=t.unidad_tematica,
            tema=t.tema,
            cantidad_respuestas=t.cantidad_respuestas,
            cantidad_incorrectas=t.cantidad_incorrectas,
            tasa_error=t.tasa_error,
        )
        for t in tasas
    ]


def presentar_desempeno_comision(
    filas: list[DesempenoComisionFila],
) -> list[DesempenoComisionFilaSalida]:
    """Arma las filas del desempeño por comisión."""
    return [
        DesempenoComisionFilaSalida(
            estudiante_id=f.estudiante_id,
            nombre=f.nombre,
            porcentaje_aciertos_acumulado=f.porcentaje_aciertos_acumulado,
            actividades_pendientes=f.actividades_pendientes,
        )
        for f in filas
    ]


def presentar_evolucion_estudiante(
    puntos: list[EvolucionTemporalPunto],
) -> list[EvolucionTemporalPuntoSalida]:
    """Arma la serie de evolución temporal individual."""
    return [
        EvolucionTemporalPuntoSalida(
            actividad_id=p.actividad_id,
            titulo_actividad=p.titulo_actividad,
            finalizada_en=p.finalizada_en,
            porcentaje_acierto=p.porcentaje_acierto,
        )
        for p in puntos
    ]


def presentar_evolucion_comision(
    puntos: list[EvolucionTemporalComisionPunto],
) -> list[EvolucionTemporalComisionPuntoSalida]:
    """Arma la serie de evolución temporal de una comisión."""
    return [
        EvolucionTemporalComisionPuntoSalida(
            actividad_id=p.actividad_id,
            titulo_actividad=p.titulo_actividad,
            porcentaje_aciertos_promedio=p.porcentaje_aciertos_promedio,
        )
        for p in puntos
    ]


def presentar_ranking_preguntas(
    filas: list[RankingPreguntaFallada],
) -> list[RankingPreguntaFalladaSalida]:
    """Arma el ranking de preguntas más falladas."""
    return [
        RankingPreguntaFalladaSalida(
            pregunta_id=f.pregunta_id,
            enunciado=f.enunciado,
            unidad_tematica=f.unidad_tematica,
            tema=f.tema,
            cantidad_presentaciones=f.cantidad_presentaciones,
            cantidad_fallos=f.cantidad_fallos,
            tasa_error=f.tasa_error,
        )
        for f in filas
    ]


def presentar_completitud(completitud: CompletitudPorActividad) -> CompletitudPorActividadSalida:
    """Arma la completitud de una actividad."""
    return CompletitudPorActividadSalida(
        detalle=[
            CompletitudFilaSalida(estudiante_id=f.estudiante_id, nombre=f.nombre, estado=f.estado)
            for f in completitud.detalle
        ],
        resumen=CompletitudResumenSalida(
            finalizadas=completitud.resumen.finalizadas,
            en_curso=completitud.resumen.en_curso,
            suspendidas=completitud.resumen.suspendidas,
            sin_iniciar=completitud.resumen.sin_iniciar,
        ),
    )
