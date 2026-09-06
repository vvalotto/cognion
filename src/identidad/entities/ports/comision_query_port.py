"""Puerto de consultas de solo lectura sobre comisiones y su roster de estudiantes.

Separado de `ComisionRepositoryPort` (altas/persistencia) por responsabilidad command/query,
mismo criterio que separa `CuentaQueryPort` de `UsuarioRepositoryPort` (`US-2.2.2`). Consumido
por `ComisionesQueryController` (HTTP) y por Analytics vía adapter in-process (`US-4.2.2`).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from src.identidad.entities.comision import Comision


@dataclass(frozen=True)
class EstudianteResumen:
    """Representación mínima de un `Usuario` con rol Estudiante para selectores en cascada."""

    id: UUID
    nombre: str


class ComisionQueryPort(ABC):
    """Consultas de solo lectura sobre `Comision` para poblar selectores docentes (RF-16, RF-17)."""

    @abstractmethod
    async def listar_comisiones_por_materia(self, materia_id: UUID) -> list[Comision]:
        """Lista las comisiones de una materia. Materia sin comisiones → lista vacía."""
        ...

    @abstractmethod
    async def listar_estudiantes(self, comision_id: UUID) -> list[EstudianteResumen]:
        """Lista los estudiantes inscriptos en una comisión. Sin inscriptos → lista vacía."""
        ...
