"""Puerto de consulta de `Usuario` con rol Estudiante, dueño de BC Identidad.

Comunicación entre BCs solo por puertos definidos en `entities/ports/` (CLAUDE.md) — este
puerto evita que Analytics importe directamente ningún módulo de `src/identidad/`. Copia
propia del BC, mismo contrato que
`src/actividad_evaluativa/entities/ports/estudiante_consulta_port.py` — cada BC arma su propio
puerto, sin import cruzado entre BCs (`US-4.2.1`).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID


class EstudianteConsultaPort(ABC):
    """Operación de consulta requerida sobre `Usuario` de BC Identidad."""

    @abstractmethod
    async def existe(self, estudiante_id: UUID) -> bool:
        """Indica si `estudiante_id` corresponde a un `Usuario` existente con rol Estudiante."""
