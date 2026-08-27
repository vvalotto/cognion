"""Eventos de dominio emitidos por el BC Actividad Evaluativa."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from src.actividad_evaluativa.entities.evaluacion import PreguntaAsignada


def _ahora() -> datetime:
    """Devuelve el instante actual en UTC."""
    return datetime.now(UTC)


@dataclass(frozen=True)
class ActividadEvaluativaCreada:
    """Se dio de alta una `ActividadEvaluativaPeriodoAbierto` nueva — primer evento de su stream."""

    actividad_id: UUID
    materia_id: UUID
    fecha_apertura: datetime
    fecha_cierre: datetime
    cantidad_preguntas: int
    cantidad_intentos_permitidos: int
    ocurrido_en: datetime = field(default_factory=_ahora)


@dataclass(frozen=True)
class EvaluacionIniciada:
    """Se fijó el set de preguntas de un Estudiante — primer evento del stream de `Evaluacion`.

    Primer evento de la `Evaluacion`: fija `preguntas_asignadas` de forma permanente
    (INV-AE-05). A partir de `US-3.2.1` el stream puede tener eventos posteriores
    (`RespuestaRegistrada`) — este sigue siendo siempre el primero.
    """

    evaluacion_id: UUID
    actividad_id: UUID
    estudiante_id: UUID
    preguntas_asignadas: list[PreguntaAsignada]
    ocurrido_en: datetime = field(default_factory=_ahora)


@dataclass(frozen=True)
class RespuestaRegistrada:
    """Se confirmó una `Respuesta` — evento repetible del stream de `Evaluacion` (INV-AE-09).

    Cada confirmación del estudiante agrega un evento nuevo, nunca modifica uno existente.
    """

    respuesta_id: UUID
    evaluacion_id: UUID
    pregunta_id: UUID
    numero_intento: int
    contenido: dict[str, Any]
    es_correcta: bool
    ocurrido_en: datetime = field(default_factory=_ahora)
