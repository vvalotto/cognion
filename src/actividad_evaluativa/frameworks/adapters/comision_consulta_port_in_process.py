"""Adaptador de `ComisionConsultaPort` — llamada in-process a BC Identidad (`US-6.1.1`).

Mismo criterio de acoplamiento consciente (`ADR-006`) que `materia_consulta_port_in_process.py`
del propio BC: vive en `frameworks/`, nunca en `entities/` ni `use_cases/`, y es uno de los
únicos puntos de Actividad Evaluativa que importa `src.identidad`. `esta_asignado_a_materia`/
`esta_asignado_a_comision` (`US-ADJ-57`) delegan en `SQLAlchemyComisionQueryRepository` de
Identidad — mismo patrón ya usado por Banco de Preguntas/Analytics, sin duplicar la query de
pertenencia (`comision_docentes`) en cada BC consumidor.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.actividad_evaluativa.entities.ports.comision_consulta_port import ComisionConsultaPort
from src.identidad.interface_adapters.gateways.comision_query_repository import (
    SQLAlchemyComisionQueryRepository,
)
from src.identidad.interface_adapters.gateways.comision_repository import (
    SQLAlchemyComisionRepository,
)


class ComisionConsultaPortInProcess(ComisionConsultaPort):
    """Implementa `ComisionConsultaPort` invocando los gateways de `Comision` de Identidad."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async compartida con los repositorios de `Comision` de Identidad."""
        self._comision_repositorio = SQLAlchemyComisionRepository(session)
        self._comision_query = SQLAlchemyComisionQueryRepository(session)

    async def obtener_materia_id(self, comision_id: UUID) -> UUID | None:
        """Devuelve el `materia_id` de la Comisión, o `None` si no existe."""
        comision = await self._comision_repositorio.obtener_por_id(comision_id)
        if comision is None:
            return None
        return comision.materia_id

    async def esta_asignado_a_materia(self, docente_id: UUID, materia_id: UUID) -> bool:
        """Ver `ComisionConsultaPort.esta_asignado_a_materia`."""
        return await self._comision_query.docente_tiene_comision_en_materia(
            docente_id, materia_id
        )

    async def esta_asignado_a_comision(self, docente_id: UUID, comision_id: UUID) -> bool:
        """Ver `ComisionConsultaPort.esta_asignado_a_comision`."""
        return await self._comision_query.docente_pertenece_a_comision(docente_id, comision_id)
