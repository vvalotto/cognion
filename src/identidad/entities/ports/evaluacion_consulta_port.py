"""Puerto de consulta de `Evaluacion`, dueña de BC Actividad Evaluativa.

Comunicación entre BCs solo por puertos definidos en `entities/ports/` (CLAUDE.md) — este
puerto evita que Identidad importe directamente ningún módulo de `src/actividad_evaluativa/`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID


class EvaluacionConsultaPort(ABC):
    """Operaciones de consulta requeridas sobre `Evaluacion` de BC Actividad Evaluativa."""

    @abstractmethod
    async def tiene_evaluaciones(self, estudiante_id: UUID) -> bool:
        """Indica si el estudiante inició alguna vez una evaluación (cualquier estado)."""
