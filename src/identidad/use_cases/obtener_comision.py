"""Caso de uso: una comisión puntual, con la autorización del Docente que consulta."""

from __future__ import annotations

from uuid import UUID

from src.identidad.entities.comision import Comision
from src.identidad.entities.errors import ComisionNoAutorizada, ComisionNoExiste
from src.identidad.entities.ports.comision_repository_port import ComisionRepositoryPort


class ObtenerComisionUseCase:
    """Devuelve una comisión validando que exista y que el Docente esté asignado a ella."""

    def __init__(self, comision_repository: ComisionRepositoryPort) -> None:
        """Recibe el repositorio de comisiones."""
        self._comision_repository = comision_repository

    async def execute(self, comision_id: UUID, docente_id: UUID | None = None) -> Comision:
        """Devuelve la comisión; `ComisionNoExiste` si no existe.

        `ComisionNoAutorizada` (`US-ADJ-57`) si `docente_id` no es `None` y no está asignado a
        esta comisión.
        """
        comision = await self._comision_repository.obtener_por_id(comision_id)
        if comision is None:
            raise ComisionNoExiste(comision_id)
        if docente_id is not None and docente_id not in comision.docentes_asignados:
            raise ComisionNoAutorizada(comision_id)
        return comision
