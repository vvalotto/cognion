"""Puerto de consulta de preguntas activas, dueño de BC Banco de Preguntas.

Comunicación entre BCs solo por puertos definidos en `entities/ports/` (CLAUDE.md) — este
puerto evita que Actividad Evaluativa importe directamente ningún módulo de
`src/banco_preguntas/`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID


class PreguntaConsultaPort(ABC):
    """Operaciones de consulta requeridas sobre `PreguntaPlantilla` de BC Banco de Preguntas."""

    @abstractmethod
    async def contar_activas_por_materia(self, materia_id: UUID) -> int:
        """Cuenta las `PreguntaPlantilla` activas del banco de la materia (INV-AE-01)."""

    @abstractmethod
    async def listar_ids_activas_por_materia(self, materia_id: UUID) -> list[UUID]:
        """Lista los ids de las `PreguntaPlantilla` activas del banco de la materia.

        Base del sampleo aleatorio (RF-12) — el Use Case hace `random.sample` sobre esta lista,
        el puerto no sabe nada de muestreo.
        """
