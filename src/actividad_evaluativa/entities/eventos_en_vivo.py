"""Eventos de dominio del modo en vivo del BC Actividad Evaluativa (`US-6.1.2` en adelante)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
)
from src.actividad_evaluativa.entities.evaluacion import PreguntaAsignada
from src.actividad_evaluativa.entities.participacion_en_vivo import (
    ParticipacionEnVivo,
    RespuestaEnVivo,
)


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


@dataclass(frozen=True)
class SesionEnVivoIniciada:
    """El Docente inició la sesión — se presenta el enunciado de la primera pregunta.

    Segundo evento del stream de la sesión. Solo el enunciado, sin las opciones: revelarlas es
    `MostrarOpcionesDeLaPregunta` (Iteración 2). La pregunta se persiste tal como se presentó.
    """

    sesion_id: UUID
    pregunta_actual_indice: int
    pregunta_id: UUID
    enunciado: str
    tipo: str
    ocurrido_en: datetime = field(default_factory=_ahora)

    @classmethod
    def desde_sesion(
        cls, sesion: ActividadEvaluativaEnVivo, enunciado: str, tipo: str
    ) -> SesionEnVivoIniciada:
        """Construye el evento a partir de una sesión recién iniciada y el enunciado presentado."""
        pregunta = sesion.pregunta_actual()  # levanta si la sesión no fue iniciada
        return cls(
            sesion_id=sesion.id,
            pregunta_actual_indice=sesion.pregunta_actual_indice or 0,
            pregunta_id=pregunta.pregunta_id,
            enunciado=enunciado,
            tipo=tipo,
        )


@dataclass(frozen=True)
class SiguientePreguntaPresentada:
    """El Docente avanzó — se presenta el enunciado de la siguiente pregunta (`US-6.2.6`).

    Mismo shape que `SesionEnVivoIniciada`: solo el enunciado, sin opciones.
    """

    sesion_id: UUID
    pregunta_actual_indice: int
    pregunta_id: UUID
    enunciado: str
    tipo: str
    ocurrido_en: datetime = field(default_factory=_ahora)

    @classmethod
    def desde_sesion(
        cls, sesion: ActividadEvaluativaEnVivo, enunciado: str, tipo: str
    ) -> SiguientePreguntaPresentada:
        """Construye el evento a partir de una sesión ya avanzada y el enunciado presentado."""
        pregunta = sesion.pregunta_actual()
        return cls(
            sesion_id=sesion.id,
            pregunta_actual_indice=sesion.pregunta_actual_indice or 0,
            pregunta_id=pregunta.pregunta_id,
            enunciado=enunciado,
            tipo=tipo,
        )


@dataclass(frozen=True)
class OpcionesEnVivoMostradas:
    """El Docente reveló las opciones de la pregunta actual — arranca el temporizador.

    `opciones` es `None` para Verdadero/Falso. Nunca indica cuál es la correcta.
    """

    sesion_id: UUID
    pregunta_actual_indice: int
    pregunta_id: UUID
    opciones: list[str] | None
    ocurrido_en: datetime = field(default_factory=_ahora)

    @classmethod
    def desde_sesion(
        cls,
        sesion: ActividadEvaluativaEnVivo,
        opciones: list[str] | None,
        ocurrido_en: datetime,
    ) -> OpcionesEnVivoMostradas:
        """Construye el evento a partir de la sesión y las opciones de la pregunta actual."""
        pregunta = sesion.pregunta_actual()
        return cls(
            sesion_id=sesion.id,
            pregunta_actual_indice=sesion.pregunta_actual_indice or 0,
            pregunta_id=pregunta.pregunta_id,
            opciones=opciones,
            ocurrido_en=ocurrido_en,
        )


@dataclass(frozen=True)
class PreguntaEnVivoCerrada:
    """El Docente cerró la pregunta actual (`US-6.2.5`).

    Payload mínimo: el ranking y el histograma no se persisten, viven en los read models.
    """

    sesion_id: UUID
    pregunta_actual_indice: int
    pregunta_id: UUID
    ocurrido_en: datetime = field(default_factory=_ahora)

    @classmethod
    def desde_sesion(
        cls, sesion: ActividadEvaluativaEnVivo, ocurrido_en: datetime
    ) -> PreguntaEnVivoCerrada:
        """Construye el evento a partir de la sesión y su pregunta actual."""
        return cls(
            sesion_id=sesion.id,
            pregunta_actual_indice=sesion.pregunta_actual_indice or 0,
            pregunta_id=sesion.pregunta_actual().pregunta_id,
            ocurrido_en=ocurrido_en,
        )


@dataclass(frozen=True)
class RespuestaEnVivoRegistrada:
    """Un Estudiante respondió la pregunta actual — evento repetible de su `ParticipacionEnVivo`."""

    sesion_id: UUID
    estudiante_id: UUID
    pregunta_id: UUID
    contenido: dict[str, Any]
    es_correcta: bool
    tiempo_respuesta_segundos: float
    puntaje: int
    ocurrido_en: datetime = field(default_factory=_ahora)

    @classmethod
    def desde_respuesta(
        cls, participacion: ParticipacionEnVivo, respuesta: RespuestaEnVivo
    ) -> RespuestaEnVivoRegistrada:
        """Construye el evento a partir de la participación y la respuesta recién registrada."""
        return cls(
            sesion_id=participacion.sesion_id,
            estudiante_id=participacion.estudiante_id,
            pregunta_id=respuesta.pregunta_id,
            contenido=respuesta.contenido,
            es_correcta=respuesta.es_correcta,
            tiempo_respuesta_segundos=respuesta.tiempo_respuesta_segundos,
            puntaje=respuesta.puntaje,
        )
