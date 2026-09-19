"""Eventos de dominio del modo en vivo del BC Actividad Evaluativa (`US-6.1.2` en adelante)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
)
from src.actividad_evaluativa.entities.evaluacion import PreguntaAsignada
from src.actividad_evaluativa.entities.participacion_en_vivo import ParticipacionEnVivo


def _ahora() -> datetime:
    """Devuelve el instante actual en UTC."""
    return datetime.now(UTC)


@dataclass(frozen=True)
class SesionEnVivoCreada:
    """Se dio de alta una `ActividadEvaluativaEnVivo` — primer evento de su stream."""

    sesion_id: UUID
    comision_id: UUID
    materia_id: UUID
    preguntas: list[PreguntaAsignada]
    tiempo_limite_por_pregunta_segundos: int
    unidad_tematica: str | None = None
    tema: str | None = None
    ocurrido_en: datetime = field(default_factory=_ahora)

    @classmethod
    def desde_sesion(cls, sesion: ActividadEvaluativaEnVivo) -> SesionEnVivoCreada:
        """Construye el evento a partir de una sesión recién creada.

        Mueve la construcción fuera de `CrearSesionEnVivoUseCase` — mismo criterio que
        `ActividadEvaluativaCreada.desde_actividad` para no acumular CBO en el Use Case.
        """
        return cls(
            sesion_id=sesion.id,
            comision_id=sesion.comision_id,
            materia_id=sesion.materia_id,
            preguntas=sesion.preguntas,
            tiempo_limite_por_pregunta_segundos=sesion.tiempo_limite_por_pregunta_segundos,
            unidad_tematica=sesion.unidad_tematica,
            tema=sesion.tema,
        )


@dataclass(frozen=True)
class EstudianteUnido:
    """Un Estudiante se unió a una sesión en vivo — primer evento de su `ParticipacionEnVivo`."""

    sesion_id: UUID
    estudiante_id: UUID
    unido_en: datetime = field(default_factory=_ahora)

    @classmethod
    def desde_participacion(cls, participacion: ParticipacionEnVivo) -> EstudianteUnido:
        """Construye el evento a partir de una `ParticipacionEnVivo` recién creada."""
        return cls(
            sesion_id=participacion.sesion_id,
            estudiante_id=participacion.estudiante_id,
            unido_en=participacion.unido_en,
        )
