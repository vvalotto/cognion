"""Puerto de consulta de `Usuario` con rol Estudiante, dueño de BC Identidad.

Comunicación entre BCs solo por puertos definidos en `entities/ports/` (CLAUDE.md) — este
puerto evita que Actividad Evaluativa importe directamente ningún módulo de `src/identidad/`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID


class EstudianteConsultaPort(ABC):
    """Operación de consulta requerida sobre `Usuario` de BC Identidad."""

    @abstractmethod
    async def existe(self, estudiante_id: UUID) -> bool:
        """Indica si `estudiante_id` corresponde a un `Usuario` existente con rol Estudiante."""

    @abstractmethod
    async def obtener_comision_id(self, estudiante_id: UUID) -> UUID | None:
        """Devuelve la `comision_id` del Estudiante, o `None` si no existe.

        Usado para filtrar la visibilidad de actividades restringidas a comisiones concretas
        (`ListarActividadesVisiblesUseCase`) — un Estudiante cursa una única Comisión
        (`estudiante.comision_id`, sin multi-inscripción todavía).
        """
