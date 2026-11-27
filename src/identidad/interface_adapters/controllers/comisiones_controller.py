"""Controller de la API para operaciones sobre comisiones."""

from __future__ import annotations

from uuid import UUID

from src.identidad.interface_adapters.presenters.identidad_presenter import (
    ComisionSalida,
    presentar_comision,
)
from src.identidad.use_cases.activar_comision import ActivarComisionUseCase
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
        activar_comision: ActivarComisionUseCase,
    ) -> None:
        """Recibe los casos de uso de creación, asignación de docente, edición, baja y reactivación."""
        self._crear_comision = crear_comision
        self._asignar_docente = asignar_docente
        self._editar_comision = editar_comision
        self._eliminar_comision = eliminar_comision
        self._activar_comision = activar_comision

    async def crear_comision(
        self, materia_id: UUID, horario: str, administrador_id: UUID
    ) -> ComisionSalida:
        """Delega la creación de la comisión en el caso de uso correspondiente."""
        comision, _evento = await self._crear_comision.execute(
            materia_id, horario, administrador_id
        )
        return presentar_comision(comision)

    async def asignar_docente(self, comision_id: UUID, docente_id: UUID) -> ComisionSalida:
        """Delega la asignación del docente en el caso de uso correspondiente."""
        comision, _evento = await self._asignar_docente.execute(comision_id, docente_id)
        return presentar_comision(comision)

    async def editar_comision(self, comision_id: UUID, horario: str) -> ComisionSalida:
        """Delega la corrección del horario en el caso de uso correspondiente."""
        return presentar_comision(await self._editar_comision.execute(comision_id, horario))

    async def eliminar_comision(self, comision_id: UUID) -> ComisionSalida | None:
        """Delega la baja (física o lógica) de una comisión en el caso de uso correspondiente."""
        resultado = await self._eliminar_comision.execute(comision_id)
        return None if resultado is None else presentar_comision(resultado)

    async def activar_comision(self, comision_id: UUID) -> ComisionSalida:
        """Delega la reactivación de una comisión deshabilitada en el caso de uso correspondiente."""
        return presentar_comision(await self._activar_comision.execute(comision_id))
