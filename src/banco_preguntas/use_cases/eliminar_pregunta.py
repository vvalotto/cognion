"""Caso de uso: eliminación (baja lógica) de una pregunta existente del banco."""

from __future__ import annotations

from uuid import UUID

from src.banco_preguntas.entities.errors import PreguntaNoExiste
from src.banco_preguntas.entities.eventos import PreguntaEliminada
from src.banco_preguntas.entities.ports.pregunta_repository_port import PreguntaRepositoryPort
from src.banco_preguntas.entities.pregunta_plantilla import (
    PreguntaPlantillaOpcionMultiple,
    PreguntaPlantillaVerdaderoFalso,
)


class EliminarPreguntaUseCase:
    """Orquesta la baja lógica de una pregunta."""

    def __init__(self, pregunta_repositorio: PreguntaRepositoryPort) -> None:
        """Recibe el repositorio de preguntas a usar."""
        self._pregunta_repositorio = pregunta_repositorio

    async def execute(
        self, pregunta_id: UUID
    ) -> tuple[
        PreguntaPlantillaOpcionMultiple | PreguntaPlantillaVerdaderoFalso, PreguntaEliminada
    ]:
        """Marca la pregunta como inactiva y persiste el cambio.

        Levanta `PreguntaNoExiste` si la pregunta no existe, `PreguntaYaEliminada` (propagada
        desde la entidad) si ya estaba inactiva.
        """
        pregunta = await self._pregunta_repositorio.obtener_por_id(pregunta_id)
        if pregunta is None:
            raise PreguntaNoExiste(pregunta_id)

        pregunta.eliminar()

        await self._pregunta_repositorio.actualizar(pregunta)

        evento = PreguntaEliminada(pregunta_id=pregunta.id, banco_id=pregunta.banco_id)
        return pregunta, evento
