"""Puerto de consulta (CQRS) para saber qué evaluaciones de un Estudiante están Finalizadas.

Separado de `EvaluacionActivaQueryPort` (`US-3.2.4`, propósito: evaluaciones NO finalizadas
para el `VerificadorDeVencimientos`) a propósito — ensancharlo repetiría el patrón de CBO ya
visto en `US-2.1.2`/`US-2.1.5`/`US-2.1.6`. Mismo criterio de separación command/query que ese
puerto y que `ActividadQueryPort` (`US-3.4.2`).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID


class EvaluacionEstudianteQueryPort(ABC):
    """Consulta de solo lectura: qué `Evaluacion` de una lista ya llegaron a `Finalizada`."""

    @abstractmethod
    async def existentes_finalizadas(self, evaluacion_ids: list[UUID]) -> set[UUID]:
        """Devuelve el subconjunto de `evaluacion_ids` con un evento `EvaluacionFinalizada`.

        `Finalizada` es un estado terminal (`entities/evaluacion.py`) — alcanza con verificar
        la existencia del evento, sin reconstruir el aggregate completo.
        """
