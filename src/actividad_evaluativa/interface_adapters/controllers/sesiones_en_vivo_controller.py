"""Controller de la API para operaciones sobre sesiones en vivo (`US-6.1.2` en adelante)."""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
)
from src.actividad_evaluativa.entities.participacion_en_vivo import ParticipacionEnVivo
from src.actividad_evaluativa.use_cases.crear_sesion_en_vivo import CrearSesionEnVivoUseCase
from src.actividad_evaluativa.use_cases.iniciar_sesion_en_vivo import (
    IniciarSesionEnVivoUseCase,
)
from src.actividad_evaluativa.use_cases.unirse_a_sesion_en_vivo import (
    UnirseASesionEnVivoUseCase,
)


class SesionesEnVivoController:
    """Adapta requests HTTP a los casos de uso sobre sesiones en vivo."""

    def __init__(
        self,
        crear_sesion: CrearSesionEnVivoUseCase,
        unirse: UnirseASesionEnVivoUseCase,
        iniciar: IniciarSesionEnVivoUseCase,
    ) -> None:
        """Recibe los casos de uso de crear, unirse e iniciar."""
        self._crear_sesion = crear_sesion
        self._unirse = unirse
        self._iniciar = iniciar

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

    async def unirse(self, sesion_id: UUID, estudiante_id: UUID) -> ParticipacionEnVivo:
        """Delega la unión del Estudiante a la sesión en el caso de uso correspondiente."""
        return await self._unirse.execute(sesion_id, estudiante_id)

    async def iniciar(self, sesion_id: UUID) -> ActividadEvaluativaEnVivo:
        """Delega el inicio de la sesión en el caso de uso correspondiente."""
        return await self._iniciar.execute(sesion_id)
