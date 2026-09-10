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


@dataclass(frozen=True)
class EstudianteConEmail:
    """Representación de un `Usuario` con rol Estudiante para BC Notificaciones (`US-5.1.1`).

    Copia con `email` separada de `EstudianteResumen` — ese DTO no lo expone porque sus
    consumidores actuales (Analytics, Banco de Preguntas) solo necesitan `id`/`nombre` para
    selectores de UI.
    """

    id: UUID
    nombre: str
    email: str


class ComisionQueryPort(ABC):
    """Consultas de solo lectura sobre `Comision` para poblar selectores docentes (RF-16, RF-17)."""

    @abstractmethod
    async def listar_comisiones_por_materia(
        self, materia_id: UUID, incluir_inactivas: bool = False
    ) -> list[Comision]:
        """Lista las comisiones activas de una materia; `incluir_inactivas=True` trae todas.

        Materia sin comisiones → lista vacía.
        """
        ...

    @abstractmethod
    async def listar_estudiantes(self, comision_id: UUID) -> list[EstudianteResumen]:
        """Lista los estudiantes inscriptos en una comisión. Sin inscriptos → lista vacía."""
        ...

    @abstractmethod
    async def listar_estudiantes_con_email(self, comision_id: UUID) -> list[EstudianteConEmail]:
        """Lista los estudiantes inscriptos en una comisión, incluido su email (`US-5.1.1`).

        Mismo roster que `listar_estudiantes` — coexisten como métodos separados por
        consumidor, no se reemplaza el existente. Sin inscriptos → lista vacía.
        """
        ...

    @abstractmethod
    async def tiene_comisiones_asignadas(self, docente_id: UUID) -> bool:
        """Indica si el docente está asignado a alguna comisión (activa o no)."""
        ...

    @abstractmethod
    async def tiene_comisiones_creadas(self, administrador_id: UUID) -> bool:
        """Indica si el administrador creó alguna comisión (activa o no).

        `comision.administrador_id` es `NOT NULL` sin `ON DELETE CASCADE` — borrar un
        Administrador que ya creó una Comisión violaría esa FK si no se detecta antes.
        """
        ...
