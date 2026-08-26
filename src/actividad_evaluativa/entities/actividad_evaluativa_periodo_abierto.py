"""Aggregate `ActividadEvaluativaPeriodoAbierto` (`BC-actividad-evaluativa-modelo.md` §5)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from src.actividad_evaluativa.entities.errors import CantidadIntentosInvalida, PeriodoInvalido


@dataclass
class ActividadEvaluativaPeriodoAbierto:
    """Ventana de disponibilidad administrada por el Docente (`ADR-015`).

    Primer evento de su propio stream en el event store (`US-3.1.1`) — no crece con la
    cantidad de estudiantes ni de respuestas (esas viven en `Evaluacion`, `US-3.1.3`).
    """

    id: UUID
    materia_id: UUID
    fecha_apertura: datetime
    fecha_cierre: datetime
    cantidad_preguntas: int
    cantidad_intentos_permitidos: int
    cerrada_manualmente: bool = field(default=False)

    @staticmethod
    def crear(
        materia_id: UUID,
        fecha_apertura: datetime,
        fecha_cierre: datetime,
        cantidad_preguntas: int,
        cantidad_intentos_permitidos: int,
    ) -> ActividadEvaluativaPeriodoAbierto:
        """Crea la actividad validando INV-AE-02/03.

        INV-AE-01 (preguntas suficientes en el banco de la materia) no se valida acá — requiere
        consultar a BC Banco de Preguntas vía puerto, responsabilidad del Use Case
        (`CrearActividadPeriodoAbiertoUseCase`).
        """
        if fecha_apertura >= fecha_cierre:
            raise PeriodoInvalido(fecha_apertura, fecha_cierre)
        if cantidad_intentos_permitidos < 1:
            raise CantidadIntentosInvalida(cantidad_intentos_permitidos)

        return ActividadEvaluativaPeriodoAbierto(
            id=uuid4(),
            materia_id=materia_id,
            fecha_apertura=fecha_apertura,
            fecha_cierre=fecha_cierre,
            cantidad_preguntas=cantidad_preguntas,
            cantidad_intentos_permitidos=cantidad_intentos_permitidos,
        )
