"""Puerto de consulta de `Comision`, dueña de BC Identidad.

Comunicación entre BCs solo por puertos definidos en `entities/ports/` (CLAUDE.md) — este
puerto evita que Banco de Preguntas importe directamente ningún módulo de `src/identidad/`.
Dirección inversa de `MateriaPort` (Identidad consultando Materia).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID


class ComisionConsultaPort(ABC):
    """Operaciones de consulta requeridas sobre `Comision` de BC Identidad."""

    @abstractmethod
    async def tiene_comisiones(self, materia_id: UUID) -> bool:
        """Indica si existe alguna comisión (activa o no) que referencie esta materia."""

    @abstractmethod
    async def esta_asignado_a_materia(self, docente_id: UUID, materia_id: UUID) -> bool:
        """Indica si el docente tiene al menos una comisión asignada en esa materia (`US-ADJ-57`).

        El banco de preguntas se gatea a nivel materia, no por comisión puntual — una
        `PreguntaPlantilla` no pertenece a una comisión.
        """
