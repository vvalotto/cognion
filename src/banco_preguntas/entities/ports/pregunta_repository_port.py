"""Puerto de persistencia de plantillas de pregunta, implementado en frameworks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.banco_preguntas.entities.pregunta_plantilla import (
    PreguntaPlantillaOpcionMultiple,
    PreguntaPlantillaVerdaderoFalso,
)
from src.banco_preguntas.entities.resultado_paginado_preguntas import (
    ResultadoPaginadoPreguntas,
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
        pagina: int | None = None,
        tamanio_pagina: int | None = None,
    ) -> ResultadoPaginadoPreguntas:
        """Lista las preguntas activas del banco que matchean todos los filtros provistos.

        Los filtros son opcionales y combinables (AND) — un filtro en `None` no restringe el
        resultado. `pagina`/`tamanio_pagina` son opt-in (US-ADJ-03): si se omiten (`None`),
        devuelve todas las preguntas que matchean, ordenadas por `fecha_creacion` — mismo
        comportamiento que antes de la paginación, usado por las pantallas que necesitan el
        banco completo (sugerencias, búsqueda por id). Si se proveen ambos, aplica
        `LIMIT`/`OFFSET` sobre ese mismo orden. `total` siempre refleja la cantidad de
        preguntas que matchean los filtros, sin paginar.
        """
