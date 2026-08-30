"""Puerto de consulta (CQRS) para el listado de `ActividadEvaluativaPeriodoAbierto` (`US-3.4.2`).

Separado del event store (append/replay por stream) porque acá la operación es una consulta
transversal a las actividades de una materia, no la reconstrucción de un único stream — mismo
criterio de separación command/query ya aplicado en `EvaluacionActivaQueryPort` (`US-3.2.4`) y
`CuentaQueryPort` (Incremento 2).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ActividadResumen:
    """Resumen de una `ActividadEvaluativaPeriodoAbierto` para el listado por materia."""

    id: UUID
    materia_id: UUID
    titulo: str
    fecha_apertura: datetime
    fecha_cierre: datetime
    cantidad_preguntas: int
    cantidad_intentos_permitidos: int
    cerrada_manualmente: bool
    cantidad_evaluaciones_activas: int
    cantidad_evaluaciones_finalizadas: int


class ActividadQueryPort(ABC):
    """Consulta de solo lectura sobre las actividades de una materia."""

    @abstractmethod
    async def listar_por_materia(self, materia_id: UUID) -> list[ActividadResumen]:
        """Devuelve el resumen de cada actividad de `materia_id`.

        Lista vacía si la materia no tiene actividades (o no existe — esta consulta no valida
        que `materia_id` corresponda a una `Materia` real, semántica de lectura).
        """
