"""Puerto de consulta (CQRS, solo lectura) del desempeño de un estudiante en evaluaciones.

Analytics no crea su propio event store (`BC-analytics-modelo.md` §2) — este puerto es la
única forma en que el resto del BC lee el event store ajeno de Actividad Evaluativa, sin
conocer SQLAlchemy ni la tabla `events`. Consumido por `US-4.1.2` y toda la Iteración 2.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class EvaluacionDesempenoResumen:
    """Resumen de una `Evaluacion` finalizada, solo con lo que Analytics necesita.

    No expone el aggregate `Evaluacion` ajeno — mismo criterio de DTO propio que
    `MateriaDTO` (`entities/ports/materia_consulta_port.py` de Actividad Evaluativa).
    """

    evaluacion_id: UUID
    actividad_id: UUID
    materia_id: UUID
    finalizada_en: datetime
    cantidad_correctas: int
    cantidad_incorrectas: int


class EvaluacionDesempenoConsultaPort(ABC):
    """Consulta de solo lectura: evaluaciones finalizadas de un estudiante, con su desempeño."""

    @abstractmethod
    async def listar_evaluaciones_finalizadas(
        self, estudiante_id: UUID, materia_id: UUID | None
    ) -> list[EvaluacionDesempenoResumen]:
        """Devuelve las `Evaluacion` finalizadas del estudiante, opcionalmente filtradas.

        Sin `materia_id`, devuelve las de todas las materias. Una `Evaluacion` sin evento
        `EvaluacionFinalizada` nunca aparece en el resultado — Analytics solo reporta sobre
        evaluaciones terminadas.
        """
