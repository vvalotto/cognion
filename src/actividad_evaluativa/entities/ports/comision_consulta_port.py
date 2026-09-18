"""Puerto de consulta de `Comision`, dueña de BC Identidad (`US-6.1.1`).

Dirección inversa de `MateriaConsultaPort` ya existente en este BC: una sesión en vivo se crea
desde una Comisión puntual (`comision_id` única y obligatoria,
`BC-actividad-evaluativa-modelo.md` §14, §17 punto 11) y `materia_id` se resuelve a partir de
ella. Comunicación entre BCs solo por puertos definidos en `entities/ports/` (`CLAUDE.md`) —
este puerto evita que Actividad Evaluativa importe directamente ningún módulo de
`src/identidad/` para este propósito.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID


class ComisionConsultaPort(ABC):
    """Operación de consulta requerida sobre `Comision` de BC Identidad."""

    @abstractmethod
    async def obtener_materia_id(self, comision_id: UUID) -> UUID | None:
        """Devuelve el `materia_id` de la Comisión, o `None` si `comision_id` no existe."""
