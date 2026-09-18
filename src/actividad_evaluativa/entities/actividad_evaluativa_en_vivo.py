"""Aggregate `ActividadEvaluativaEnVivo` (`BC-actividad-evaluativa-modelo.md` §14)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID, uuid4

from src.actividad_evaluativa.entities.errors import TiempoLimiteInvalido
from src.actividad_evaluativa.entities.evaluacion import PreguntaAsignada


class EstadoSesionEnVivo(StrEnum):
    """Estados posibles de una sesión en vivo."""

    EN_ESPERA = "EnEspera"
    EN_CURSO = "EnCurso"
    FINALIZADA = "Finalizada"


@dataclass
class ActividadEvaluativaEnVivo:
    """Sesión sincrónica dirigida por el Docente para una Comisión puntual (`ADR-015`).

    Igual que `ActividadEvaluativaPeriodoAbierto`, no crece con la cantidad de estudiantes ni de
    respuestas — esas viven en `ParticipacionEnVivo`. `US-6.1.2` solo ejercita la construcción
    inicial (`EnEspera`, sin pregunta actual); las transiciones posteriores las agregan
    `US-6.1.4` y la Iteración 2.
    """

    id: UUID
    comision_id: UUID
    materia_id: UUID
    preguntas: list[PreguntaAsignada]
    tiempo_limite_por_pregunta_segundos: int
    unidad_tematica: str | None = field(default=None)
    """`None` (default) significa "cualquier unidad", combinable con `tema` (AND)."""
    tema: str | None = field(default=None)
    """`None` (default) significa "cualquier tema" del banco de la Materia."""
    estado: EstadoSesionEnVivo = field(default=EstadoSesionEnVivo.EN_ESPERA)
    pregunta_actual_indice: int | None = field(default=None)
    opciones_mostradas: bool = field(default=False)
    pregunta_actual_cerrada: bool = field(default=False)

    @staticmethod
    def crear(
        comision_id: UUID,
        materia_id: UUID,
        preguntas: list[PreguntaAsignada],
        tiempo_limite_por_pregunta_segundos: int,
        unidad_tematica: str | None = None,
        tema: str | None = None,
    ) -> ActividadEvaluativaEnVivo:
        """Crea la sesión en `EnEspera` con el set de preguntas ya fijado, validando INV-AEV-02.

        INV-AEV-01 (preguntas suficientes en el banco) no se valida acá — requiere consultar a
        BC Banco de Preguntas vía puerto, responsabilidad del Use Case
        (`CrearSesionEnVivoUseCase`).
        """
        if tiempo_limite_por_pregunta_segundos <= 0:
            raise TiempoLimiteInvalido(tiempo_limite_por_pregunta_segundos)

        return ActividadEvaluativaEnVivo(
            id=uuid4(),
            comision_id=comision_id,
            materia_id=materia_id,
            preguntas=preguntas,
            tiempo_limite_por_pregunta_segundos=tiempo_limite_por_pregunta_segundos,
            unidad_tematica=unidad_tematica or None,
            tema=tema or None,
        )
