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
    """Operaciones de consulta requeridas sobre `Comision` de BC Identidad."""

    @abstractmethod
    async def obtener_materia_id(self, comision_id: UUID) -> UUID | None:
        """Devuelve el `materia_id` de la Comisión, o `None` si `comision_id` no existe."""

    @abstractmethod
    async def esta_asignado_a_materia(self, docente_id: UUID, materia_id: UUID) -> bool:
        """Indica si el docente tiene al menos una comisión asignada en esa materia (`US-ADJ-57`).

        Nivel de autorización usado por las actividades de período abierto — no tienen
        restricción de comisión puntual (aplican a toda la materia, decisión de Víctor
        2026-09-27), a diferencia de las sesiones en vivo.
        """

    @abstractmethod
    async def esta_asignado_a_comision(self, docente_id: UUID, comision_id: UUID) -> bool:
        """Indica si el docente está asignado a esa comisión puntual (`US-ADJ-57`).

        Nivel de autorización usado por las sesiones en vivo — se dan en una Comisión concreta,
        a diferencia de las actividades de período abierto.
        """
