"""Adaptador de `ComisionConsultaPort` — llamada in-process a BC Identidad.

Mismo criterio de acoplamiento consciente (`ADR-006`) que
`estudiante_consulta_port_in_process.py`: vive en `frameworks/`, nunca en `entities/` ni
`use_cases/`, y es uno de los únicos puntos de Analytics que importa `src.identidad`
(`US-4.2.2`).
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.analytics.entities.ports.comision_consulta_port import (
    ComisionConsultaPort,
    ComisionResumen,
    EstudianteResumen,
)
from src.identidad.interface_adapters.gateways.comision_query_repository import (
    SQLAlchemyComisionQueryRepository,
)


class ComisionConsultaPortInProcess(ComisionConsultaPort):
    """Implementa `ComisionConsultaPort` invocando `ComisionQueryPort` de Identidad in-process."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async compartida con el repositorio de `Comision` de Identidad."""
        self._comision_query = SQLAlchemyComisionQueryRepository(session)

    async def listar_comisiones_por_materia(self, materia_id: UUID) -> list[ComisionResumen]:
        """Lista las comisiones de una materia, mapeadas al DTO propio de Analytics."""
        comisiones = await self._comision_query.listar_comisiones_por_materia(materia_id)
        return [ComisionResumen(id=c.id, horario=c.horario) for c in comisiones]

    async def listar_estudiantes(self, comision_id: UUID) -> list[EstudianteResumen]:
        """Lista los estudiantes de una comisión, mapeados al DTO propio de Analytics."""
        estudiantes = await self._comision_query.listar_estudiantes(comision_id)
        return [EstudianteResumen(id=e.id, nombre=e.nombre) for e in estudiantes]
