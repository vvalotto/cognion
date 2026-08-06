"""Puerto de persistencia de plantillas de pregunta, implementado en frameworks."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.banco_preguntas.entities.pregunta_plantilla import PreguntaPlantillaOpcionMultiple


class PreguntaRepositoryPort(ABC):
    """Operaciones de persistencia requeridas sobre plantillas de pregunta."""

    @abstractmethod
    async def guardar(self, pregunta: PreguntaPlantillaOpcionMultiple) -> None:
        """Guarda una pregunta de opción múltiple nueva."""
