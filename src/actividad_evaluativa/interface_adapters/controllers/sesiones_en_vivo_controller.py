"""Controller de la API para operaciones sobre sesiones en vivo (`US-6.1.2` en adelante)."""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
)
from src.actividad_evaluativa.use_cases.crear_sesion_en_vivo import CrearSesionEnVivoUseCase


class SesionesEnVivoController:
    """Adapta requests HTTP a los casos de uso sobre sesiones en vivo."""

    def __init__(self, crear_sesion: CrearSesionEnVivoUseCase) -> None:
        """Recibe el caso de uso de creación de sesión."""
        self._crear_sesion = crear_sesion

    async def crear(
        self,
        comision_id: UUID,
        cantidad_preguntas: int,
        tiempo_limite_por_pregunta_segundos: int,
        unidad_tematica: str | None = None,
        tema: str | None = None,
    ) -> ActividadEvaluativaEnVivo:
        """Delega la creación de la sesión en el caso de uso correspondiente."""
        return await self._crear_sesion.execute(
            comision_id,
            cantidad_preguntas,
            tiempo_limite_por_pregunta_segundos,
            unidad_tematica,
            tema,
        )
