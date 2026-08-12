"""Caso de uso: consulta de solo lectura de una materia por id."""

from __future__ import annotations

from uuid import UUID

from src.banco_preguntas.entities.materia import Materia
from src.banco_preguntas.entities.ports.materia_repository_port import MateriaRepositoryPort


class ObtenerMateriaUseCase:
    """Resuelve una `Materia` por id — consumido por otros BCs a través de un puerto."""

    def __init__(self, materia_repositorio: MateriaRepositoryPort) -> None:
        """Recibe el repositorio de materias a usar."""
        self._materia_repositorio = materia_repositorio

    async def execute(self, materia_id: UUID) -> Materia | None:
        """Busca la materia por id, o `None` si no existe."""
        return await self._materia_repositorio.obtener_por_id(materia_id)
