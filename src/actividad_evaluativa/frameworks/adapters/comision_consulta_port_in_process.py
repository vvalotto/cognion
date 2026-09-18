"""Adaptador de `ComisionConsultaPort` — llamada in-process a BC Identidad (`US-6.1.1`).

Mismo criterio de acoplamiento consciente (`ADR-006`) que `materia_consulta_port_in_process.py`
del propio BC: vive en `frameworks/`, nunca en `entities/` ni `use_cases/`, y es uno de los
únicos puntos de Actividad Evaluativa que importa `src.identidad`.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.actividad_evaluativa.entities.ports.comision_consulta_port import ComisionConsultaPort
from src.identidad.interface_adapters.gateways.comision_repository import (
    SQLAlchemyComisionRepository,
)


class ComisionConsultaPortInProcess(ComisionConsultaPort):
    """Implementa `ComisionConsultaPort` invocando `ComisionRepositoryPort` de Identidad."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async compartida con el repositorio de `Comision` de Identidad."""
        self._comision_repositorio = SQLAlchemyComisionRepository(session)

    async def obtener_materia_id(self, comision_id: UUID) -> UUID | None:
        """Devuelve el `materia_id` de la Comisión, o `None` si no existe."""
        comision = await self._comision_repositorio.obtener_por_id(comision_id)
        if comision is None:
            return None
        return comision.materia_id
