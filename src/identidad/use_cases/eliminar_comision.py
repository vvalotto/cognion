"""Caso de uso: baja de una comisión — física si no tiene estudiantes, lógica si tiene."""

from __future__ import annotations

from uuid import UUID

from src.identidad.entities.comision import Comision
from src.identidad.entities.errors import ComisionNoExiste
from src.identidad.entities.ports.comision_query_port import ComisionQueryPort
from src.identidad.entities.ports.comision_repository_port import ComisionRepositoryPort


class EliminarComisionUseCase:
    """Da de baja una comisión: física si no tiene estudiantes, lógica (`activa=False`) si sí."""

    def __init__(
        self,
        comision_repositorio: ComisionRepositoryPort,
        comision_query: ComisionQueryPort,
    ) -> None:
        """Recibe el repositorio de comisiones y el puerto de consulta a usar."""
        self._comision_repositorio = comision_repositorio
        self._comision_query = comision_query

    async def execute(self, comision_id: UUID) -> Comision | None:
        """Elimina o deshabilita `comision_id` según tenga estudiantes inscriptos.

        Devuelve la `Comision` deshabilitada si se optó por baja lógica, o `None` si se
        eliminó físicamente. Lanza `ComisionNoExiste` si la comisión no existe.
        """
        comision = await self._comision_repositorio.obtener_por_id(comision_id)
        if comision is None:
            raise ComisionNoExiste(comision_id)

        estudiantes = await self._comision_query.listar_estudiantes(comision_id)
        if estudiantes:
            comision.deshabilitar()
            await self._comision_repositorio.actualizar(comision)
            return comision

        await self._comision_repositorio.eliminar(comision_id)
        return None
