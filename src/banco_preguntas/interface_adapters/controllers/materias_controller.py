"""Controller de la API para operaciones sobre materias."""

from __future__ import annotations

from src.banco_preguntas.entities.banco import Banco
from src.banco_preguntas.entities.eventos import BancoCreado, MateriaCreada
from src.banco_preguntas.entities.materia import Materia
from src.banco_preguntas.use_cases.crear_materia import CrearMateriaUseCase
from src.banco_preguntas.use_cases.listar_materias import ListarMateriasUseCase


class MateriasController:
    """Adapta requests HTTP a los casos de uso de alta y listado de materias."""

    def __init__(
        self, crear_materia: CrearMateriaUseCase, listar_materias: ListarMateriasUseCase
    ) -> None:
        """Recibe los casos de uso de creación y listado de materias."""
        self._crear_materia = crear_materia
        self._listar_materias = listar_materias

    async def crear_materia(self, nombre: str) -> tuple[Materia, Banco, MateriaCreada, BancoCreado]:
        """Delega la creación de la materia y su banco en el caso de uso correspondiente."""
        return await self._crear_materia.execute(nombre)

    async def listar_materias(self) -> list[tuple[Materia, Banco, int]]:
        """Delega el listado de materias (con conteo de preguntas activas) en el caso de uso."""
        return await self._listar_materias.execute()
