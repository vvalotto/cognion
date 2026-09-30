"""Caso de uso: corrección del horario de una comisión existente."""

from __future__ import annotations

from uuid import UUID

from src.identidad.entities.comision import Comision
from src.identidad.entities.errors import ComisionNoExiste
from src.identidad.entities.ports.comision_repository_port import ComisionRepositoryPort


class EditarComisionUseCase:
    """Corrige el horario de una comisión existente."""

    def __init__(self, comision_repositorio: ComisionRepositoryPort) -> None:
        """Recibe el repositorio de comisiones a usar."""
        self._comision_repositorio = comision_repositorio

    async def execute(self, comision_id: UUID, horario: str) -> Comision:
        """Corrige el horario de `comision_id` y devuelve la comisión actualizada.

        Lanza `ComisionNoExiste` si la comisión no existe.
        """
        comision = await self._comision_repositorio.obtener_por_id(comision_id)
        if comision is None:
            raise ComisionNoExiste(comision_id)

        comision.cambiar_horario(horario)
        await self._comision_repositorio.actualizar(comision)
        return comision
