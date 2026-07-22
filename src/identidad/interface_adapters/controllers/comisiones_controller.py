"""Controller de la API para operaciones sobre comisiones."""

from __future__ import annotations

from uuid import UUID

from src.identidad.entities.comision import Comision
from src.identidad.entities.eventos import ComisionCreada, DocenteAsignado
from src.identidad.use_cases.asignar_docente_a_comision import AsignarDocenteAComisionUseCase
from src.identidad.use_cases.crear_comision import CrearComisionUseCase


class ComisionesController:
    """Adapta requests HTTP a los casos de uso de comisiones."""

    def __init__(
        self,
        crear_comision: CrearComisionUseCase,
        asignar_docente: AsignarDocenteAComisionUseCase,
    ) -> None:
        """Recibe los casos de uso de creación de comisión y asignación de docente."""
        self._crear_comision = crear_comision
        self._asignar_docente = asignar_docente

    async def crear_comision(
        self, materia: str, horario: str, administrador_id: UUID
    ) -> tuple[Comision, ComisionCreada]:
        """Delega la creación de la comisión en el caso de uso correspondiente."""
        return await self._crear_comision.execute(materia, horario, administrador_id)

    async def asignar_docente(
        self, comision_id: UUID, docente_id: UUID
    ) -> tuple[Comision, DocenteAsignado]:
        """Delega la asignación del docente en el caso de uso correspondiente."""
        return await self._asignar_docente.execute(comision_id, docente_id)
