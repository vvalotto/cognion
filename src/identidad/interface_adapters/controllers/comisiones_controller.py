"""Controller de la API para operaciones sobre comisiones."""

from __future__ import annotations

from uuid import UUID

from src.identidad.entities.comision import Comision
from src.identidad.entities.eventos import ComisionCreada, DocenteAsignado
from src.identidad.use_cases.asignar_docente_a_comision import AsignarDocenteAComisionUseCase
from src.identidad.use_cases.crear_comision import CrearComisionUseCase
from src.identidad.use_cases.editar_comision import EditarComisionUseCase
from src.identidad.use_cases.eliminar_comision import EliminarComisionUseCase


class ComisionesController:
    """Adapta requests HTTP a los casos de uso de comisiones."""

    def __init__(
        self,
        crear_comision: CrearComisionUseCase,
        asignar_docente: AsignarDocenteAComisionUseCase,
        editar_comision: EditarComisionUseCase,
        eliminar_comision: EliminarComisionUseCase,
    ) -> None:
        """Recibe los casos de uso de creación, asignación de docente, edición y baja."""
        self._crear_comision = crear_comision
        self._asignar_docente = asignar_docente
        self._editar_comision = editar_comision
        self._eliminar_comision = eliminar_comision

    async def crear_comision(
        self, materia_id: UUID, horario: str, administrador_id: UUID
    ) -> tuple[Comision, ComisionCreada]:
        """Delega la creación de la comisión en el caso de uso correspondiente."""
        return await self._crear_comision.execute(materia_id, horario, administrador_id)

    async def asignar_docente(
        self, comision_id: UUID, docente_id: UUID
    ) -> tuple[Comision, DocenteAsignado]:
        """Delega la asignación del docente en el caso de uso correspondiente."""
        return await self._asignar_docente.execute(comision_id, docente_id)

    async def editar_comision(self, comision_id: UUID, horario: str) -> Comision:
        """Delega la corrección del horario en el caso de uso correspondiente."""
        return await self._editar_comision.execute(comision_id, horario)

    async def eliminar_comision(self, comision_id: UUID) -> Comision | None:
        """Delega la baja (física o lógica) de una comisión en el caso de uso correspondiente."""
        return await self._eliminar_comision.execute(comision_id)
