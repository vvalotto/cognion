"""Puerto de consulta de `Comision` y su roster de estudiantes, dueña de BC Identidad.

Comunicación entre BCs solo por puertos definidos en `entities/ports/` (CLAUDE.md) — este
puerto evita que Analytics importe directamente ningún módulo de `src/identidad/`. Copia
propia del BC con DTOs propios, mismo criterio que
`src/analytics/entities/ports/evaluacion_desempeno_consulta_port.py` (`US-4.2.2`).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ComisionResumen:
    """Representación mínima de una `Comision` ajena a Analytics."""

    id: UUID
    horario: str


@dataclass(frozen=True)
class EstudianteResumen:
    """Representación mínima de un `Usuario` con rol Estudiante ajeno a Analytics."""

    id: UUID
    nombre: str


class ComisionConsultaPort(ABC):
    """Operaciones de consulta requeridas sobre `Comision` de BC Identidad."""

    @abstractmethod
    async def listar_comisiones_por_materia(self, materia_id: UUID) -> list[ComisionResumen]:
        """Lista las comisiones de una materia. Materia sin comisiones → lista vacía."""
        ...

    @abstractmethod
    async def listar_estudiantes(self, comision_id: UUID) -> list[EstudianteResumen]:
        """Lista los estudiantes inscriptos en una comisión. Sin inscriptos → lista vacía."""
        ...

    @abstractmethod
    async def esta_asignado_a_materia(self, docente_id: UUID, materia_id: UUID) -> bool:
        """Indica si el docente tiene al menos una comisión asignada en esa materia (`US-ADJ-57`).

        Nivel de autorización usado por los informes que no reciben `comision_id`, o cuando
        `comision_id` viene en `None` — mismo criterio que Actividad Evaluativa.
        """
        ...

    @abstractmethod
    async def esta_asignado_a_comision(self, docente_id: UUID, comision_id: UUID) -> bool:
        """Indica si el docente está asignado a esa comisión puntual (`US-ADJ-57`).

        Nivel de autorización usado por los informes que acotan a una `comision_id` concreta.
        """
        ...
