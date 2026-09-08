"""Caso de uso: reactivar una comisión previamente deshabilitada."""

from __future__ import annotations

from uuid import UUID

from src.identidad.entities.comision import Comision
from src.identidad.entities.errors import ComisionNoExiste
from src.identidad.entities.ports.comision_repository_port import ComisionRepositoryPort


class ActivarComisionUseCase:
    """Reactiva una comisión deshabilitada, volviéndola a mostrar en los listados normales."""

    def __init__(self, comision_repositorio: ComisionRepositoryPort) -> None:
        """Recibe el repositorio de comisiones a usar."""
        self._comision_repositorio = comision_repositorio

    async def execute(self, comision_id: UUID) -> Comision:
        """Activa `comision_id`. Lanza `ComisionNoExiste` si no existe."""
        comision = await self._comision_repositorio.obtener_por_id(comision_id)
        if comision is None:
            raise ComisionNoExiste(comision_id)

        comision.activar()
        await self._comision_repositorio.actualizar(comision)
        return comision
