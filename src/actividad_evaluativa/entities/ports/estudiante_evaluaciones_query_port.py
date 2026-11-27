"""Puerto de consulta (CQRS): ¿el estudiante inició alguna vez una evaluación? (`US-9.4.3`).

Lo consume Identidad, vía su `EvaluacionConsultaPort`, para impedir eliminar la cuenta de un
estudiante con evaluaciones sin leer el event store de este BC (`ADR-026`). Separado de
`EvaluacionEstudianteQueryPort` (qué evaluaciones ya están Finalizadas) a propósito: cada puerto
de consulta tiene una sola razón de cambio.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID


class EstudianteEvaluacionesQueryPort(ABC):
    """Consulta de solo lectura sobre las evaluaciones iniciadas por un estudiante."""

    @abstractmethod
    async def tiene_evaluaciones_iniciadas(self, estudiante_id: UUID) -> bool:
        """Indica si el estudiante inició alguna vez una evaluación (cualquier estado)."""
        ...
