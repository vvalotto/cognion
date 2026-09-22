"""Controller de la API para las consultas de una sesión en vivo (command/query separado)."""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import EstadoSesionEnVivo
from src.actividad_evaluativa.entities.ports.participantes_sesion_query_port import (
    ParticipanteResumen,
)
from src.actividad_evaluativa.entities.ports.proyecciones_en_vivo_port import (
    ParticipanteEnRanking,
)
from src.actividad_evaluativa.entities.ports.sesiones_en_vivo_query_port import (
    SesionEnVivoResumen,
)
from src.actividad_evaluativa.use_cases.listar_participantes import ListarParticipantesUseCase
from src.actividad_evaluativa.use_cases.listar_sesiones_en_vivo import ListarSesionesEnVivoUseCase
from src.actividad_evaluativa.use_cases.obtener_estado_sesion import (
    EstadoSesion,
    ObtenerEstadoSesionUseCase,
)
from src.actividad_evaluativa.use_cases.obtener_ranking import ObtenerRankingUseCase
from src.shared.entities.tipo_perfil import TipoPerfil


class SesionesEnVivoQueryController:
    """Adapta requests HTTP de lectura a los casos de uso de consulta de la sesión en vivo."""

    def __init__(
        self,
        obtener_estado: ObtenerEstadoSesionUseCase,
        listar_participantes: ListarParticipantesUseCase,
        obtener_ranking: ObtenerRankingUseCase,
        listar_sesiones: ListarSesionesEnVivoUseCase,
    ) -> None:
        """Recibe los casos de uso de estado, participantes, ranking y listado de sesiones."""
        self._obtener_estado = obtener_estado
        self._listar_participantes = listar_participantes
        self._obtener_ranking = obtener_ranking
        self._listar_sesiones = listar_sesiones

    async def obtener_estado(
        self, sesion_id: UUID, estudiante_id: UUID | None = None
    ) -> EstadoSesion:
        """Devuelve el estado de la sesión; con `estudiante_id`, incluye su avance propio."""
        return await self._obtener_estado.execute(sesion_id, estudiante_id)

    async def listar_participantes(self, sesion_id: UUID) -> list[ParticipanteResumen]:
        """Devuelve los participantes de la sala de espera."""
        return await self._listar_participantes.execute(sesion_id)

    async def obtener_ranking(
        self, sesion_id: UUID, es_estudiante: bool
    ) -> list[ParticipanteEnRanking]:
        """Devuelve el ranking de la sesión (el Estudiante, solo al finalizar)."""
        return await self._obtener_ranking.execute(sesion_id, es_estudiante)

    async def listar_sesiones(
        self,
        usuario_id: UUID,
        rol: TipoPerfil,
        comision_id: UUID | None,
        estados: list[EstadoSesionEnVivo],
    ) -> list[SesionEnVivoResumen]:
        """Devuelve las sesiones en vivo visibles para `usuario_id` según su rol."""
        return await self._listar_sesiones.execute(usuario_id, rol, comision_id, estados)
