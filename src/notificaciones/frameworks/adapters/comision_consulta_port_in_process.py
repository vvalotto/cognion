"""Adaptador de `ComisionConsultaPort` — llamada in-process a BC Identidad (`US-5.1.1`).

Mismo criterio de acoplamiento consciente (`ADR-006`) que
`src/analytics/frameworks/adapters/comision_consulta_port_in_process.py` (`US-4.2.2`): vive
en `frameworks/`, nunca en `entities/` ni `use_cases/`, y es uno de los únicos puntos de
Notificaciones que importa `src.identidad`.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.identidad.interface_adapters.gateways.comision_query_repository import (
    SQLAlchemyComisionQueryRepository,
)
from src.notificaciones.entities.ports.comision_consulta_port import (
    ComisionConsultaPort,
    DestinatarioNotificacion,
)


class ComisionConsultaPortInProcess(ComisionConsultaPort):
    """Implementa `ComisionConsultaPort` invocando `ComisionQueryPort` de Identidad in-process."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async compartida con el repositorio de `Comision` de Identidad."""
        self._comision_query = SQLAlchemyComisionQueryRepository(session)

    async def listar_comisiones_por_materia(self, materia_id: UUID) -> list[UUID]:
        """Lista los ids de las comisiones activas de una materia."""
        comisiones = await self._comision_query.listar_comisiones_por_materia(materia_id)
        return [comision.id for comision in comisiones]

    async def listar_destinatarios(
        self, comision_ids: list[UUID]
    ) -> list[DestinatarioNotificacion]:
        """Lista el roster combinado de las comisiones indicadas, sin estudiantes repetidos.

        Un `dict` indexado por `estudiante_id` preserva la primera aparición de cada
        estudiante si estuviera inscripto en más de una de las comisiones dadas.
        """
        destinatarios: dict[UUID, DestinatarioNotificacion] = {}
        for comision_id in comision_ids:
            estudiantes = await self._comision_query.listar_estudiantes_con_email(comision_id)
            for estudiante in estudiantes:
                destinatarios.setdefault(
                    estudiante.id,
                    DestinatarioNotificacion(
                        estudiante_id=estudiante.id,
                        nombre=estudiante.nombre,
                        email=estudiante.email,
                    ),
                )
        return list(destinatarios.values())
