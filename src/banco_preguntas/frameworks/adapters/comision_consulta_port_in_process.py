"""Adaptador de `ComisionConsultaPort` — llamada in-process a BC Identidad.

Mismo criterio de acoplamiento consciente (`ADR-006`) que `materia_port_in_process.py`
(dirección inversa, Identidad consultando Materia): vive en `frameworks/` de Banco de
Preguntas, nunca en `entities/` ni `use_cases/`, y es el único punto de Banco de Preguntas
que importa `src.identidad`. `esta_asignado_a_materia` (`US-ADJ-57`) delega en
`SQLAlchemyComisionQueryRepository` de Identidad en vez de consultar `ComisionModel`
directo — mismo patrón ya usado por Actividad Evaluativa/Analytics para no duplicar la
query de pertenencia (`comision_docentes`) en cada BC consumidor. `tiene_comisiones`
(`US-9.4.1`, `ADR-026`) también delega en ese gateway: este adaptador no lee modelos ORM de
Identidad.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.banco_preguntas.entities.ports.comision_consulta_port import ComisionConsultaPort
from src.identidad.interface_adapters.gateways.comision_query_repository import (
    SQLAlchemyComisionQueryRepository,
)


class ComisionConsultaPortInProcess(ComisionConsultaPort):
    """Implementa `ComisionConsultaPort` delegando en el gateway de consultas de Identidad."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async compartida con el resto de repositorios de este proceso."""
        self._comision_query = SQLAlchemyComisionQueryRepository(session)

    async def tiene_comisiones(self, materia_id: UUID) -> bool:
        """Indica si existe alguna comisión (activa o no) que referencie esta materia."""
        return await self._comision_query.existe_comision_en_materia(materia_id)

    async def esta_asignado_a_materia(self, docente_id: UUID, materia_id: UUID) -> bool:
        """Ver `ComisionConsultaPort.esta_asignado_a_materia`."""
        return await self._comision_query.docente_tiene_comision_en_materia(docente_id, materia_id)
