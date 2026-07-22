"""Caso de uso: alta de una comisión nueva."""

from __future__ import annotations

from uuid import UUID

from src.identidad.entities.comision import Comision
from src.identidad.entities.eventos import ComisionCreada
from src.identidad.entities.ports.comision_repository_port import ComisionRepositoryPort


class CrearComisionUseCase:
    """Registra una comisión nueva a nombre de un administrador."""

    def __init__(self, repositorio: ComisionRepositoryPort) -> None:
        """Recibe el repositorio de comisiones a usar."""
        self._repositorio = repositorio

    async def execute(
        self, materia: str, horario: str, administrador_id: UUID
    ) -> tuple[Comision, ComisionCreada]:
        """Crea y persiste la comisión, y devuelve la comisión junto al evento emitido."""
        comision = Comision.crear(materia, horario, administrador_id)
        await self._repositorio.guardar(comision)

        evento = ComisionCreada(comision_id=comision.id, materia=comision.materia)
        return comision, evento
