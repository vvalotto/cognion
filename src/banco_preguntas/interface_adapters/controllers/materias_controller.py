"""Controller de la API para operaciones sobre materias."""

from __future__ import annotations

from uuid import UUID

from src.banco_preguntas.entities.banco import Banco
from src.banco_preguntas.entities.eventos import BancoCreado, MateriaCreada
from src.banco_preguntas.entities.materia import Materia
from src.banco_preguntas.use_cases.activar_materia import ActivarMateriaUseCase
from src.banco_preguntas.use_cases.crear_materia import CrearMateriaUseCase
from src.banco_preguntas.use_cases.editar_materia import EditarMateriaUseCase
from src.banco_preguntas.use_cases.eliminar_materia import EliminarMateriaUseCase
from src.banco_preguntas.use_cases.listar_materias import ListarMateriasUseCase


class MateriasController:
    """Adapta requests HTTP a los casos de uso de alta, listado, edición y baja de materias."""

    def __init__(
        self,
        crear_materia: CrearMateriaUseCase,
        listar_materias: ListarMateriasUseCase,
        editar_materia: EditarMateriaUseCase,
        eliminar_materia: EliminarMateriaUseCase,
        activar_materia: ActivarMateriaUseCase,
    ) -> None:
        """Recibe los casos de uso de creación, listado, edición, baja y reactivación."""
        self._crear_materia = crear_materia
        self._listar_materias = listar_materias
        self._editar_materia = editar_materia
        self._eliminar_materia = eliminar_materia
        self._activar_materia = activar_materia

    async def crear_materia(self, nombre: str) -> tuple[Materia, Banco, MateriaCreada, BancoCreado]:
        """Delega la creación de la materia y su banco en el caso de uso correspondiente."""
        return await self._crear_materia.execute(nombre)

    async def listar_materias(self, incluir_inactivas: bool = False) -> list[tuple[Materia, Banco, int]]:
        """Delega el listado de materias (con conteo de preguntas activas) en el caso de uso."""
        return await self._listar_materias.execute(incluir_inactivas)

    async def editar_materia(self, materia_id: UUID, nombre: str) -> Materia:
        """Delega la corrección del nombre de una materia en el caso de uso correspondiente."""
        return await self._editar_materia.execute(materia_id, nombre)

    async def eliminar_materia(self, materia_id: UUID) -> Materia | None:
        """Delega la baja (física o lógica) de una materia en el caso de uso correspondiente."""
        return await self._eliminar_materia.execute(materia_id)

    async def activar_materia(self, materia_id: UUID) -> Materia:
        """Delega la reactivación de una materia deshabilitada en el caso de uso correspondiente."""
        return await self._activar_materia.execute(materia_id)
