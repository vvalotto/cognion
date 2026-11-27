"""Presenters de actividades de período abierto (`ADR-031`): entidades y resúmenes -> salidas de la API.

Los `dataclass` de salida tienen los mismos campos que los esquemas de `frameworks/api/schemas.py`;
FastAPI los valida contra el `response_model` sin código extra. Sin Pydantic ni FastAPI.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_periodo_abierto import (
    ActividadEvaluativaPeriodoAbierto,
)
from src.actividad_evaluativa.entities.ports.actividad_query_port import ActividadResumen
from src.actividad_evaluativa.use_cases.listar_actividades_visibles import ActividadVisible


@dataclass(frozen=True)
class ActividadSalida:
    """Una actividad de período abierto."""

    id: UUID
    materia_id: UUID
    fecha_apertura: datetime
    fecha_cierre: datetime
    cantidad_preguntas: int
    cantidad_intentos_permitidos: int
    cerrada_manualmente: bool
    titulo: str
    comisiones_ids: list[UUID]
    unidad_tematica: str | None
    tema: str | None


@dataclass(frozen=True)
class ActividadResumenSalida:
    """Una actividad con su estado derivado y el conteo de evaluaciones."""

    id: UUID
    materia_id: UUID
    titulo: str
    fecha_apertura: datetime
    fecha_cierre: datetime
    cantidad_preguntas: int
    cantidad_intentos_permitidos: int
    estado: str
    cerrada_manualmente: bool
    cantidad_evaluaciones_activas: int
    cantidad_evaluaciones_finalizadas: int
    comisiones_ids: list[UUID]
    unidad_tematica: str | None
    tema: str | None


@dataclass(frozen=True)
class ActividadVisibleSalida:
    """Una actividad tal como la ve un Estudiante."""

    id: UUID
    materia_id: UUID
    titulo: str
    fecha_apertura: datetime
    fecha_cierre: datetime
    estado: str
    evaluacion_id: UUID | None


def presentar_actividad(actividad: ActividadEvaluativaPeriodoAbierto) -> ActividadSalida:
    """Arma la salida de una actividad."""
    return ActividadSalida(
        id=actividad.id,
        materia_id=actividad.materia_id,
        fecha_apertura=actividad.fecha_apertura,
        fecha_cierre=actividad.fecha_cierre,
        cantidad_preguntas=actividad.cantidad_preguntas,
        cantidad_intentos_permitidos=actividad.cantidad_intentos_permitidos,
        cerrada_manualmente=actividad.cerrada_manualmente,
        titulo=actividad.titulo,
        comisiones_ids=list(actividad.comisiones_ids),
        unidad_tematica=actividad.unidad_tematica,
        tema=actividad.tema,
    )


def estado_de_actividad(resumen: ActividadResumen, ahora: datetime) -> str:
    """Deriva el estado de una actividad — no persiste un campo propio (`US-3.4.2`).

    `cerrada` si se cerró manualmente o si `fecha_cierre` ya pasó; `programada` si todavía no
    abrió; `en_curso` en cualquier otro caso.
    """
    if resumen.cerrada_manualmente or resumen.fecha_cierre <= ahora:
        return "cerrada"
    if resumen.fecha_apertura > ahora:
        return "programada"
    return "en_curso"


def presentar_actividad_resumen(
    resumen: ActividadResumen, ahora: datetime
) -> ActividadResumenSalida:
    """Arma la salida de un resumen de actividad con su estado derivado a `ahora`."""
    return ActividadResumenSalida(
        id=resumen.id,
        materia_id=resumen.materia_id,
        titulo=resumen.titulo,
        fecha_apertura=resumen.fecha_apertura,
        fecha_cierre=resumen.fecha_cierre,
        cantidad_preguntas=resumen.cantidad_preguntas,
        cantidad_intentos_permitidos=resumen.cantidad_intentos_permitidos,
        estado=estado_de_actividad(resumen, ahora),
        cerrada_manualmente=resumen.cerrada_manualmente,
        cantidad_evaluaciones_activas=resumen.cantidad_evaluaciones_activas,
        cantidad_evaluaciones_finalizadas=resumen.cantidad_evaluaciones_finalizadas,
        comisiones_ids=list(resumen.comisiones_ids),
        unidad_tematica=resumen.unidad_tematica,
        tema=resumen.tema,
    )


def presentar_actividades_resumen(
    resumenes: list[ActividadResumen], ahora: datetime
) -> list[ActividadResumenSalida]:
    """Arma el listado de resúmenes de actividad, todos con el mismo `ahora`."""
    return [presentar_actividad_resumen(r, ahora) for r in resumenes]


def presentar_actividades_visibles(
    visibles: list[ActividadVisible],
) -> list[ActividadVisibleSalida]:
    """Arma el listado de actividades visibles para el Estudiante."""
    return [
        ActividadVisibleSalida(
            id=v.id,
            materia_id=v.materia_id,
            titulo=v.titulo,
            fecha_apertura=v.fecha_apertura,
            fecha_cierre=v.fecha_cierre,
            estado=v.estado,
            evaluacion_id=v.evaluacion_id,
        )
        for v in visibles
    ]
