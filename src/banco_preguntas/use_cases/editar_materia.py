"""Caso de uso: corrección del nombre de una materia existente."""

from __future__ import annotations

from uuid import UUID

from src.banco_preguntas.entities.errors import MateriaNoExiste, MateriaYaExiste
from src.banco_preguntas.entities.materia import Materia
from src.banco_preguntas.entities.ports.materia_repository_port import MateriaRepositoryPort


class EditarMateriaUseCase:
    """Corrige el nombre de una materia existente (INV-BP-00: nombre único)."""

    def __init__(self, materia_repositorio: MateriaRepositoryPort) -> None:
        """Recibe el repositorio de materias a usar."""
        self._materia_repositorio = materia_repositorio

    async def execute(self, materia_id: UUID, nombre: str) -> Materia:
        """Renombra `materia_id` a `nombre` y devuelve la materia actualizada.

        Lanza `MateriaNoExiste` si la materia no existe, `MateriaYaExiste` si el nombre
        nuevo ya pertenece a otra materia (no valida contra sí misma, si el nombre no
        cambió).
        """
        materia = await self._materia_repositorio.obtener_por_id(materia_id)
        if materia is None:
            raise MateriaNoExiste(materia_id)

        if nombre != materia.nombre:
            existente = await self._materia_repositorio.obtener_por_nombre(nombre)
            if existente is not None:
                raise MateriaYaExiste(nombre)

        materia.renombrar(nombre)
        await self._materia_repositorio.actualizar(materia)
        return materia
