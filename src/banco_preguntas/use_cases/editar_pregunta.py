"""Caso de uso: edición de una pregunta existente del banco."""

from __future__ import annotations

from uuid import UUID

from src.banco_preguntas.entities.errors import PreguntaNoExiste
from src.banco_preguntas.entities.eventos import PreguntaEditada
from src.banco_preguntas.entities.metadatos_pregunta import MetadatosPregunta
from src.banco_preguntas.entities.opcion import Opcion
from src.banco_preguntas.entities.ports.pregunta_repository_port import PreguntaRepositoryPort
from src.banco_preguntas.entities.pregunta_plantilla import (
    PreguntaPlantillaOpcionMultiple,
    PreguntaPlantillaVerdaderoFalso,
)


class EditarPreguntaUseCase:
    """Orquesta la edición de una pregunta, delegando invariantes en su tipo concreto."""

    def __init__(self, pregunta_repositorio: PreguntaRepositoryPort) -> None:
        """Recibe el repositorio de preguntas a usar."""
        self._pregunta_repositorio = pregunta_repositorio

    async def execute(
        self,
        pregunta_id: UUID,
        metadatos: MetadatosPregunta,
        opciones: list[Opcion] | None = None,
        respuesta_correcta: bool | None = None,
    ) -> tuple[PreguntaPlantillaOpcionMultiple | PreguntaPlantillaVerdaderoFalso, PreguntaEditada]:
        """Edita la pregunta según su tipo concreto y persiste los cambios.

        Levanta `PreguntaNoExiste`, `PreguntaInactiva` u `OpcionesInvalidas` (esta última
        propagada desde la entidad).
        """
        pregunta = await self._pregunta_repositorio.obtener_por_id(pregunta_id)
        if pregunta is None:
            raise PreguntaNoExiste(pregunta_id)

        if isinstance(pregunta, PreguntaPlantillaOpcionMultiple):
            pregunta.editar(metadatos=metadatos, opciones=opciones or [])
        else:
            pregunta.editar(metadatos=metadatos, respuesta_correcta=bool(respuesta_correcta))

        await self._pregunta_repositorio.actualizar(pregunta)

        evento = PreguntaEditada(pregunta_id=pregunta.id, banco_id=pregunta.banco_id)
        return pregunta, evento
