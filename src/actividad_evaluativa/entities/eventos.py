"""Eventos de dominio emitidos por el BC Actividad Evaluativa."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID


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
