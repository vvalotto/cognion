"""Caso de uso: alta de una comisión nueva."""

from __future__ import annotations

from uuid import UUID

from src.identidad.entities.comision import Comision
from src.identidad.entities.errors import MateriaNoExiste
from src.identidad.entities.eventos import ComisionCreada
from src.identidad.entities.ports.comision_repository_port import ComisionRepositoryPort
from src.identidad.entities.ports.materia_port import MateriaPort


class CrearComisionUseCase:
    """Registra una comisión nueva a nombre de un administrador."""

    def __init__(self, repositorio: ComisionRepositoryPort, materia_port: MateriaPort) -> None:
        """Recibe el repositorio de comisiones y el puerto de consulta de materias a usar."""
        self._repositorio = repositorio
        self._materia_port = materia_port

    async def execute(
        self, materia_id: UUID, horario: str, administrador_id: UUID
    ) -> tuple[Comision, ComisionCreada]:
        """Crea y persiste la comisión, y devuelve la comisión junto al evento emitido.

        Lanza `MateriaNoExiste` si `materia_id` no resuelve contra `MateriaPort`.
        """
        if await self._materia_port.obtener(materia_id) is None:
            raise MateriaNoExiste(materia_id)

        comision = Comision.crear(materia_id, horario, administrador_id)
        await self._repositorio.guardar(comision)

        evento = ComisionCreada(comision_id=comision.id, materia_id=comision.materia_id)
        return comision, evento
