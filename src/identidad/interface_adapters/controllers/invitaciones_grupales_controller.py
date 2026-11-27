"""Controller de la API para los links de invitación grupales (`US-ADJ-67`)."""

from __future__ import annotations

from uuid import UUID

from src.identidad.interface_adapters.presenters.identidad_presenter import (
    InvitacionGrupalEstadoSalida,
    InvitacionGrupalSalida,
    presentar_invitacion_grupal,
    presentar_invitacion_grupal_estado,
)
from src.identidad.use_cases.generar_invitacion_grupal import GenerarInvitacionGrupalUseCase
from src.identidad.use_cases.obtener_ultima_invitacion_grupal import (
    ObtenerUltimaInvitacionGrupalUseCase,
)
from src.identidad.use_cases.revocar_invitacion_grupal import RevocarInvitacionGrupalUseCase


class InvitacionesGrupalesController:
    """Adapta requests HTTP a los casos de uso del link grupal (generar, desactivar, consultar)."""

    def __init__(
        self,
        generar: GenerarInvitacionGrupalUseCase,
        revocar: RevocarInvitacionGrupalUseCase,
        obtener_ultima: ObtenerUltimaInvitacionGrupalUseCase,
    ) -> None:
        """Recibe los tres casos de uso del link grupal."""
        self._generar = generar
        self._revocar = revocar
        self._obtener_ultima = obtener_ultima

    async def generar(
        self, comision_id: UUID, solicitante_id: UUID, duracion_minutos: int
    ) -> InvitacionGrupalSalida:
        """Delega la generación del link grupal en el caso de uso."""
        invitacion, _evento = await self._generar.execute(
            comision_id, solicitante_id, duracion_minutos
        )
        return presentar_invitacion_grupal(invitacion)

    async def revocar(self, comision_id: UUID, invitacion_id: UUID, solicitante_id: UUID) -> None:
        """Delega la desactivación del link grupal en el caso de uso."""
        await self._revocar.execute(comision_id, invitacion_id, solicitante_id)

    async def obtener_ultima(
        self, comision_id: UUID, solicitante_id: UUID
    ) -> InvitacionGrupalEstadoSalida | None:
        """Delega la consulta del último link grupal en el caso de uso."""
        resultado = await self._obtener_ultima.execute(comision_id, solicitante_id)
        return None if resultado is None else presentar_invitacion_grupal_estado(resultado)
