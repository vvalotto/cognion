"""Puerto de persistencia de plantillas de pregunta, implementado en frameworks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.banco_preguntas.entities.pregunta_plantilla import (
    PreguntaPlantillaOpcionMultiple,
    PreguntaPlantillaVerdaderoFalso,
)


class PreguntaRepositoryPort(ABC):
    """Operaciones de persistencia requeridas sobre plantillas de pregunta."""

    @abstractmethod
    async def guardar(
        self, pregunta: PreguntaPlantillaOpcionMultiple | PreguntaPlantillaVerdaderoFalso
    ) -> None:
        """Guarda una pregunta nueva (opción múltiple o verdadero/falso)."""

    @abstractmethod
    async def obtener_por_id(
        self, pregunta_id: UUID
    ) -> PreguntaPlantillaOpcionMultiple | PreguntaPlantillaVerdaderoFalso | None:
        """Busca una pregunta por id; devuelve `None` si no existe."""

    @abstractmethod
    async def actualizar(
        self, pregunta: PreguntaPlantillaOpcionMultiple | PreguntaPlantillaVerdaderoFalso
    ) -> None:
        """Guarda los cambios de una pregunta ya existente (actualización, no alta)."""

    @abstractmethod
    async def filtrar(
        self,
        banco_id: UUID,
        unidad: str | None = None,
        tema: str | None = None,
        dificultad: str | None = None,
        importancia: str | None = None,
    ) -> list[PreguntaPlantillaOpcionMultiple | PreguntaPlantillaVerdaderoFalso]:
        """Lista las preguntas activas del banco que matchean todos los filtros provistos.

        Los filtros son opcionales y combinables (AND) — un filtro en `None` no restringe el
        resultado.
        """
