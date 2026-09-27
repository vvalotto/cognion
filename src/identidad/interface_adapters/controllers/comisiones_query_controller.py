"""Controller de consultas de solo lectura sobre comisiones (`US-4.2.2`).

Separado de `ComisionesController` (comandos: crear comisión, asignar docente) por
responsabilidad command/query, mismo criterio que separa `CuentasController` de
`UsuariosController` (`US-2.2.2`).
"""

from __future__ import annotations

from uuid import UUID

from src.identidad.entities.comision import Comision
from src.identidad.entities.errors import (
    ComisionNoAutorizada,
    ComisionNoExiste,
    MateriaNoAutorizada,
    MateriaNoExiste,
)
from src.identidad.entities.ports.comision_query_port import ComisionQueryPort, EstudianteResumen
from src.identidad.entities.ports.comision_repository_port import ComisionRepositoryPort
from src.identidad.entities.ports.materia_port import MateriaPort


class ComisionesQueryController:
    """Adapta requests HTTP a las consultas de solo lectura sobre comisiones."""

    def __init__(
        self,
        comision_query: ComisionQueryPort,
        materia_port: MateriaPort,
        comision_repository: ComisionRepositoryPort,
    ) -> None:
        """Recibe el puerto de query y los puertos usados para validar existencia."""
        self._comision_query = comision_query
        self._materia_port = materia_port
        self._comision_repository = comision_repository

    async def listar_comisiones_por_materia(
        self,
        materia_id: UUID,
        incluir_inactivas: bool = False,
        docente_id: UUID | None = None,
    ) -> list[Comision]:
        """Lista las comisiones de una materia; `MateriaNoExiste` si `materia_id` no existe.

        `docente_id` (`US-ADJ-57`) acota el resultado a las comisiones propias del Docente que
        llama — `None` (Administrador) devuelve todas sin filtrar. `MateriaNoAutorizada` si el
        Docente no tiene ninguna comisión en esta materia.
        """
        if await self._materia_port.obtener(materia_id) is None:
            raise MateriaNoExiste(materia_id)
        comisiones = await self._comision_query.listar_comisiones_por_materia(
            materia_id, incluir_inactivas
        )
        if docente_id is None:
            return comisiones
        propias = [c for c in comisiones if docente_id in c.docentes_asignados]
        if not propias:
            raise MateriaNoAutorizada(materia_id)
        return propias

    async def listar_estudiantes(
        self, comision_id: UUID, docente_id: UUID | None = None
    ) -> list[EstudianteResumen]:
        """Lista los estudiantes de una comisión; `ComisionNoExiste` si `comision_id` no existe.

        `ComisionNoAutorizada` (`US-ADJ-57`) si `docente_id` no es `None` y no está asignado a
        esta comisión puntual.
        """
        comision = await self._comision_repository.obtener_por_id(comision_id)
        if comision is None:
            raise ComisionNoExiste(comision_id)
        if docente_id is not None and docente_id not in comision.docentes_asignados:
            raise ComisionNoAutorizada(comision_id)
        return await self._comision_query.listar_estudiantes(comision_id)

    async def obtener_comision(self, comision_id: UUID, docente_id: UUID | None = None) -> Comision:
        """Devuelve una comisión puntual; `ComisionNoExiste` si `comision_id` no existe.

        Consulta de lectura simple (`US-ADJ-25`) — pass-through sobre
        `ComisionRepositoryPort.obtener_por_id()`, ya inyectado para validar existencia en
        `listar_estudiantes`, sin agregar un Use Case dedicado. `ComisionNoAutorizada`
        (`US-ADJ-57`) si `docente_id` no es `None` y no está asignado a esta comisión.
        """
        comision = await self._comision_repository.obtener_por_id(comision_id)
        if comision is None:
            raise ComisionNoExiste(comision_id)
        if docente_id is not None and docente_id not in comision.docentes_asignados:
            raise ComisionNoAutorizada(comision_id)
        return comision
