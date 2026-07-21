from __future__ import annotations

from uuid import UUID

from src.identidad.entities.comision import Comision
from src.identidad.entities.eventos import ComisionCreada
from src.identidad.entities.ports.comision_repository_port import ComisionRepositoryPort


class CrearComisionUseCase:
    def __init__(self, repositorio: ComisionRepositoryPort) -> None:
        self._repositorio = repositorio

    async def execute(
        self, materia: str, horario: str, administrador_id: UUID
    ) -> tuple[Comision, ComisionCreada]:
        comision = Comision.crear(materia, horario, administrador_id)
        await self._repositorio.guardar(comision)

        evento = ComisionCreada(comision_id=comision.id, materia=comision.materia)
        return comision, evento
