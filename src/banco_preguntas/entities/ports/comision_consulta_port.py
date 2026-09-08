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
