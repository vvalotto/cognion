"""Controller de consultas de solo lectura sobre comisiones (`US-4.2.2`).

Separado de `ComisionesController` (comandos: crear comisión, asignar docente) por
responsabilidad command/query, mismo criterio que separa `CuentasController` de
`UsuariosController` (`US-2.2.2`).
"""

from __future__ import annotations

from uuid import UUID

from src.identidad.entities.comision import Comision
from src.identidad.entities.errors import ComisionNoExiste, MateriaNoExiste
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

    async def listar_comisiones_por_materia(self, materia_id: UUID) -> list[Comision]:
        """Lista las comisiones de una materia; `MateriaNoExiste` si `materia_id` no existe."""
        if await self._materia_port.obtener(materia_id) is None:
            raise MateriaNoExiste(materia_id)
        return await self._comision_query.listar_comisiones_por_materia(materia_id)

    async def listar_estudiantes(self, comision_id: UUID) -> list[EstudianteResumen]:
        """Lista los estudiantes de una comisión; `ComisionNoExiste` si `comision_id` no existe."""
        if await self._comision_repository.obtener_por_id(comision_id) is None:
            raise ComisionNoExiste(comision_id)
        return await self._comision_query.listar_estudiantes(comision_id)
