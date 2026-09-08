"""Caso de uso: reactivar una materia previamente deshabilitada."""

from __future__ import annotations

from uuid import UUID

from src.banco_preguntas.entities.errors import MateriaNoExiste
from src.banco_preguntas.entities.materia import Materia
from src.banco_preguntas.entities.ports.materia_repository_port import MateriaRepositoryPort


class ActivarMateriaUseCase:
    """Reactiva una materia deshabilitada, volviéndola a mostrar en los listados normales."""

    def __init__(self, materia_repositorio: MateriaRepositoryPort) -> None:
        """Recibe el repositorio de materias a usar."""
        self._materia_repositorio = materia_repositorio

    async def execute(self, materia_id: UUID) -> Materia:
        """Activa `materia_id`. Lanza `MateriaNoExiste` si no existe."""
        materia = await self._materia_repositorio.obtener_por_id(materia_id)
        if materia is None:
            raise MateriaNoExiste(materia_id)

        materia.activar()
        await self._materia_repositorio.actualizar(materia)
        return materia
