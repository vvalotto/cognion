"""Caso de uso: estudiantes de una comisión, con la autorización del Docente que consulta."""

from __future__ import annotations

from uuid import UUID

from src.identidad.entities.errors import ComisionNoAutorizada, ComisionNoExiste
from src.identidad.entities.ports.comision_query_port import ComisionQueryPort, EstudianteResumen
from src.identidad.entities.ports.comision_repository_port import ComisionRepositoryPort


class ListarEstudiantesDeComisionUseCase:
    """Lista los estudiantes de una comisión validando que exista y que el Docente esté asignado."""

    def __init__(
        self, comision_repository: ComisionRepositoryPort, comision_query: ComisionQueryPort
    ) -> None:
        """Recibe el repositorio de comisiones y el puerto de consulta."""
        self._comision_repository = comision_repository
        self._comision_query = comision_query

    async def execute(
        self, comision_id: UUID, docente_id: UUID | None = None
    ) -> list[EstudianteResumen]:
        """Devuelve los estudiantes; `ComisionNoExiste` si la comisión no existe.

        `ComisionNoAutorizada` (`US-ADJ-57`) si `docente_id` no es `None` y no está asignado a
        esta comisión puntual.
        """
        comision = await self._comision_repository.obtener_por_id(comision_id)
        if comision is None:
            raise ComisionNoExiste(comision_id)
        if docente_id is not None and docente_id not in comision.docentes_asignados:
            raise ComisionNoAutorizada(comision_id)
        return await self._comision_query.listar_estudiantes(comision_id)
