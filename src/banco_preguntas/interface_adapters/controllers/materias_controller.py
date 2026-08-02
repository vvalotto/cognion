"""Controller de la API para operaciones sobre materias."""

from __future__ import annotations

from src.banco_preguntas.entities.banco import Banco
from src.banco_preguntas.entities.eventos import BancoCreado, MateriaCreada
from src.banco_preguntas.entities.materia import Materia
from src.banco_preguntas.use_cases.crear_materia import CrearMateriaUseCase


class MateriasController:
    """Adapta requests HTTP al caso de uso de alta de materias."""

    def __init__(self, crear_materia: CrearMateriaUseCase) -> None:
        """Recibe el caso de uso de creación de materia."""
        self._crear_materia = crear_materia

    async def crear_materia(self, nombre: str) -> tuple[Materia, Banco, MateriaCreada, BancoCreado]:
        """Delega la creación de la materia y su banco en el caso de uso correspondiente."""
        return await self._crear_materia.execute(nombre)
