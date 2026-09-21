"""Controller de la API para los comandos con que el Docente conduce una sesión en vivo."""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
)
from src.actividad_evaluativa.use_cases.avanzar_siguiente_pregunta import (
    AvanzarSiguientePreguntaUseCase,
)
from src.actividad_evaluativa.use_cases.cerrar_pregunta_actual import (
    CerrarPreguntaActualUseCase,
)
from src.actividad_evaluativa.use_cases.finalizar_sesion_en_vivo import (
    FinalizarSesionEnVivoUseCase,
)
from src.actividad_evaluativa.use_cases.mostrar_opciones_en_vivo import (
    MostrarOpcionesEnVivoUseCase,
)


class ConduccionEnVivoController:
    """Adapta requests HTTP del Docente a los casos de uso que conducen la sesión."""

    def __init__(
        self,
        mostrar_opciones: MostrarOpcionesEnVivoUseCase,
        cerrar_pregunta: CerrarPreguntaActualUseCase,
        avanzar_siguiente_pregunta: AvanzarSiguientePreguntaUseCase,
        finalizar_sesion: FinalizarSesionEnVivoUseCase,
    ) -> None:
        """Recibe los casos de uso de mostrar opciones, cerrar, avanzar y finalizar."""
        self._mostrar_opciones = mostrar_opciones
        self._cerrar_pregunta = cerrar_pregunta
        self._avanzar_siguiente_pregunta = avanzar_siguiente_pregunta
        self._finalizar_sesion = finalizar_sesion

    async def mostrar_opciones(self, sesion_id: UUID) -> ActividadEvaluativaEnVivo:
        """Delega la revelación de opciones en el caso de uso correspondiente."""
        return await self._mostrar_opciones.execute(sesion_id)

    async def cerrar_pregunta(self, sesion_id: UUID) -> ActividadEvaluativaEnVivo:
        """Delega el cierre de la pregunta actual en el caso de uso correspondiente."""
        return await self._cerrar_pregunta.execute(sesion_id)

    async def avanzar_siguiente_pregunta(self, sesion_id: UUID) -> ActividadEvaluativaEnVivo:
        """Avanza a la siguiente pregunta de la sesión."""
        return await self._avanzar_siguiente_pregunta.execute(sesion_id)

    async def finalizar_sesion(self, sesion_id: UUID) -> ActividadEvaluativaEnVivo:
        """Finaliza la sesión y transmite el ranking final."""
        return await self._finalizar_sesion.execute(sesion_id)
