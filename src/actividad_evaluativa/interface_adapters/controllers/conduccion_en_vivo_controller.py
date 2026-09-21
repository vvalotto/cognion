"""Controller de la API para los comandos con que el Docente conduce una sesión en vivo."""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
)
from src.actividad_evaluativa.use_cases.mostrar_opciones_en_vivo import (
    MostrarOpcionesEnVivoUseCase,
)


class ConduccionEnVivoController:
    """Adapta requests HTTP del Docente a los casos de uso que conducen la sesión."""

    def __init__(self, mostrar_opciones: MostrarOpcionesEnVivoUseCase) -> None:
        """Recibe el caso de uso de mostrar opciones (`US-6.2.2`)."""
        self._mostrar_opciones = mostrar_opciones

    async def mostrar_opciones(self, sesion_id: UUID) -> ActividadEvaluativaEnVivo:
        """Delega la revelación de opciones en el caso de uso correspondiente."""
        return await self._mostrar_opciones.execute(sesion_id)
