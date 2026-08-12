"""Puerto de consulta de `Materia`, dueña de BC Banco de Preguntas.

Comunicación entre BCs solo por puertos definidos en `entities/ports/` (CLAUDE.md) — este
puerto evita que Identidad importe directamente ningún módulo de `src/banco_preguntas/`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class MateriaDTO:
    """Representación mínima de una `Materia` ajena a Identidad."""

    id: UUID
    nombre: str


class MateriaPort(ABC):
    """Operaciones de consulta requeridas sobre `Materia` de BC Banco de Preguntas."""

    @abstractmethod
    async def obtener(self, materia_id: UUID) -> MateriaDTO | None:
        """Busca una materia por id, o `None` si no existe."""
