"""Controller de la API para operaciones sobre materias."""

from __future__ import annotations

from uuid import UUID

from src.banco_preguntas.interface_adapters.presenters.banco_presenter import (
    MateriaBasicaSalida,
    MateriaListItemSalida,
    MateriaSalida,
    presentar_materia_basica,
    presentar_materia_creada,
    presentar_materias,
)
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

    async def crear_materia(self, nombre: str) -> MateriaSalida:
        """Crea la materia con su banco y presenta ambos; los eventos se descartan acá."""
        materia, banco, _evento_materia, _evento_banco = await self._crear_materia.execute(nombre)
        return presentar_materia_creada(materia, banco)

    async def listar_materias(
        self, incluir_inactivas: bool = False, docente_id: UUID | None = None
    ) -> list[MateriaListItemSalida]:
        """Lista las materias (con conteo de preguntas activas) y las presenta.

        `docente_id` acota el listado a las materias del Docente que llama (`US-ADJ-57`).
        """
        items = await self._listar_materias.execute(incluir_inactivas, docente_id)
        return presentar_materias(items)

    async def editar_materia(self, materia_id: UUID, nombre: str) -> MateriaBasicaSalida:
        """Corrige el nombre de una materia y la presenta."""
        return presentar_materia_basica(await self._editar_materia.execute(materia_id, nombre))

    async def eliminar_materia(self, materia_id: UUID) -> MateriaBasicaSalida | None:
        """Da de baja una materia: `None` si se borró físicamente, la materia presentada si no."""
        materia = await self._eliminar_materia.execute(materia_id)
        return None if materia is None else presentar_materia_basica(materia)

    async def activar_materia(self, materia_id: UUID) -> MateriaBasicaSalida:
        """Reactiva una materia deshabilitada y la presenta."""
        return presentar_materia_basica(await self._activar_materia.execute(materia_id))
