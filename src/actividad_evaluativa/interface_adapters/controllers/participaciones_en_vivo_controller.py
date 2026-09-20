"""Controller de la API para las respuestas de un Estudiante en una sesión en vivo (`US-6.2.4`)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from src.actividad_evaluativa.use_cases.responder_pregunta_en_vivo import (
    ResponderPreguntaEnVivoUseCase,
    ResultadoRespuestaEnVivo,
)


class ParticipacionesEnVivoController:
    """Adapta requests HTTP de un Estudiante a los casos de uso sobre su participación."""

    def __init__(self, responder: ResponderPreguntaEnVivoUseCase) -> None:
        """Recibe el caso de uso de responder una pregunta."""
        self._responder = responder

    async def responder(
        self,
        sesion_id: UUID,
        estudiante_id: UUID,
        pregunta_id: UUID,
        contenido: dict[str, Any],
    ) -> ResultadoRespuestaEnVivo:
        """Delega el registro de la respuesta en el caso de uso correspondiente."""
        return await self._responder.execute(sesion_id, estudiante_id, pregunta_id, contenido)
