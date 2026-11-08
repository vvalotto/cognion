"""Autorización común de los casos de uso que operan sobre una comisión (`US-ADJ-67`)."""

from __future__ import annotations

from uuid import UUID

from src.identidad.entities.comision import Comision
from src.identidad.entities.errors import ComisionNoAutorizada, ComisionNoExiste
from src.identidad.entities.ports.comision_repository_port import ComisionRepositoryPort


async def exigir_docente_asignado(
    comision_repositorio: ComisionRepositoryPort, comision_id: UUID, solicitante_id: UUID
) -> Comision:
    """Devuelve la comisión si el Docente que la pide está asignado a ella.

    Lanza `ComisionNoExiste` si no existe y `ComisionNoAutorizada` (`US-ADJ-57`) si
    `solicitante_id`, el usuario del JWT, no figura entre sus docentes asignados.
    """
    comision = await comision_repositorio.obtener_por_id(comision_id)
    if comision is None:
        raise ComisionNoExiste(comision_id)
    if solicitante_id not in comision.docentes_asignados:
        raise ComisionNoAutorizada(comision_id)
    return comision
