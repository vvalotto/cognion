"""Adaptador de `PreguntaMetadatoConsultaPort` — llamada in-process a Banco de Preguntas.

Mismo criterio de acoplamiento consciente (`ADR-006`) que
`comision_consulta_port_in_process.py`: vive en `frameworks/`, nunca en `entities/` ni
`use_cases/`, y es el único punto de Analytics que importa `src.banco_preguntas` (`US-4.2.3`).
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.analytics.entities.ports.pregunta_metadato_consulta_port import (
    MetadatoPreguntaResumen,
    PreguntaMetadatoConsultaPort,
)
from src.banco_preguntas.frameworks.db.models import PreguntaPlantillaModel


class PreguntaMetadatoConsultaPortInProcess(PreguntaMetadatoConsultaPort):
    """Implementa `PreguntaMetadatoConsultaPort` leyendo `pregunta_plantilla` in-process."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async compartida con el repositorio de Banco de Preguntas."""
        self._session = session

    async def obtener_metadatos(
        self, pregunta_ids: list[UUID]
    ) -> dict[UUID, MetadatoPreguntaResumen]:
        """Ver `PreguntaMetadatoConsultaPort.obtener_metadatos`."""
        if not pregunta_ids:
            return {}

        resultado = await self._session.execute(
            select(PreguntaPlantillaModel).where(PreguntaPlantillaModel.id.in_(pregunta_ids))
        )
        return {
            modelo.id: MetadatoPreguntaResumen(
                unidad_tematica=modelo.unidad_tematica, tema=modelo.tema
            )
            for modelo in resultado.scalars().all()
        }
