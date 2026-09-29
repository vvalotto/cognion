"""Caso de uso: detalle de una actividad puntual (`US-3.4.4`, RF-11b)."""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.entities.errors import ActividadNoExiste, MateriaNoAutorizada
from src.actividad_evaluativa.entities.ports.actividad_query_port import (
    ActividadQueryPort,
    ActividadResumen,
)
from src.actividad_evaluativa.entities.ports.comision_consulta_port import ComisionConsultaPort


class ObtenerActividadUseCase:
    """Consulta de solo lectura sobre una actividad puntual, con el chequeo de pertenencia."""

    def __init__(
        self, actividad_query: ActividadQueryPort, comision_consulta: ComisionConsultaPort
    ) -> None:
        """Recibe el puerto de consulta de actividades y el puerto de Comisión."""
        self._actividad_query = actividad_query
        self._comision_consulta = comision_consulta

    async def execute(
        self, actividad_id: UUID, docente_id: UUID | None = None
    ) -> ActividadResumen:
        """Devuelve el resumen de `actividad_id`.

        Levanta `ActividadNoExiste` si no está, `MateriaNoAutorizada` (403) si `docente_id` no
        tiene ninguna Comisión asignada en la materia de la actividad (`US-ADJ-57`); `None`
        (Administrador) no filtra.
        """
        actividad = await self._actividad_query.obtener(actividad_id)
        if actividad is None:
            raise ActividadNoExiste(actividad_id)
        if docente_id is not None and not await self._comision_consulta.esta_asignado_a_materia(
            docente_id, actividad.materia_id
        ):
            raise MateriaNoAutorizada(actividad.materia_id)
        return actividad
