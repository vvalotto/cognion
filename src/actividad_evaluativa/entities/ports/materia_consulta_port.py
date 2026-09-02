"""Puerto de consulta de `Materia`, dueña de BC Banco de Preguntas.

Comunicación entre BCs solo por puertos definidos en `entities/ports/` (CLAUDE.md) — este
puerto evita que Actividad Evaluativa importe directamente ningún módulo de
`src/banco_preguntas/`. Mismo contrato que `identidad/entities/ports/materia_port.py`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class MateriaDTO:
    """Representación mínima de una `Materia` ajena a Actividad Evaluativa."""

    id: UUID
    nombre: str


class MateriaConsultaPort(ABC):
    """Operaciones de consulta requeridas sobre `Materia` de BC Banco de Preguntas."""

    @abstractmethod
    async def obtener(self, materia_id: UUID) -> MateriaDTO | None:
        """Busca una materia por id, o `None` si no existe."""
