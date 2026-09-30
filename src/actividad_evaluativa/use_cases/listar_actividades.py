"""Caso de uso: listado de actividades de una materia (`US-3.4.2`, RF-11)."""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.entities.errors import MateriaNoAutorizada
from src.actividad_evaluativa.entities.ports.actividad_query_port import (
    ActividadQueryPort,
    ActividadResumen,
)
from src.actividad_evaluativa.entities.ports.comision_consulta_port import ComisionConsultaPort


class ListarActividadesUseCase:
    """Delega el listado en el puerto de consulta, con el chequeo de pertenencia del Docente."""

    def __init__(
        self, actividad_query: ActividadQueryPort, comision_consulta: ComisionConsultaPort
    ) -> None:
        """Recibe el puerto de consulta de actividades y el puerto de Comisión."""
        self._actividad_query = actividad_query
        self._comision_consulta = comision_consulta

    async def execute(
        self, materia_id: UUID, docente_id: UUID | None = None
    ) -> list[ActividadResumen]:
        """Devuelve el resumen de cada actividad de `materia_id`.

        Levanta `MateriaNoAutorizada` (403) si `docente_id` no tiene ninguna Comisión asignada
        en esa materia (`US-ADJ-57`); `None` (Administrador) no filtra.
        """
        if docente_id is not None and not await self._comision_consulta.esta_asignado_a_materia(
            docente_id, materia_id
        ):
            raise MateriaNoAutorizada(materia_id)
        return await self._actividad_query.listar_por_materia(materia_id)
