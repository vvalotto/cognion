"""Puerto de consulta (CQRS) para listar sesiones en vivo de una Comisión (`US-6.3.2`).

Separado de `EventStorePort` (append/replay por stream) porque acá la operación es una
consulta transversal a todos los streams de `ActividadEvaluativaEnVivo` de una Comisión, no la
reconstrucción de uno solo — mismo criterio de separación command/query que
`EvaluacionActivaQueryPort` (`US-3.2.4`).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import EstadoSesionEnVivo


@dataclass(frozen=True)
class SesionEnVivoResumen:
    """Una sesión en vivo, para el listado por Comisión.

    `materia_nombre` queda vacío en las instancias que arma este read model local — lo resuelve
    el use case contra Banco de Preguntas (`US-6.3.2`), nunca este puerto ni su adapter.
    """

    id: UUID
    comision_id: UUID
    materia_id: UUID
    cantidad_preguntas: int
    tiempo_limite_por_pregunta_segundos: int
    estado: EstadoSesionEnVivo
    creada_en: datetime
    unidad_tematica: str | None = None
    tema: str | None = None
    materia_nombre: str = ""


class SesionesEnVivoQueryPort(ABC):
    """Consulta de solo lectura de las sesiones en vivo de una Comisión."""

    @abstractmethod
    async def listar(
        self, comision_id: UUID, estados: list[EstadoSesionEnVivo]
    ) -> list[SesionEnVivoResumen]:
        """Devuelve las sesiones de `comision_id` cuyo estado está en `estados`.

        Orden: más recientes primero (`creada_en` descendente). Lista vacía si no hay ninguna.
        """
