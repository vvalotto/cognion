"""Controller de la API para operaciones sobre invitaciones."""

from __future__ import annotations

from uuid import UUID

from src.identidad.interface_adapters.presenters.identidad_presenter import (
    InvitacionPreviewSalida,
    InvitacionSalida,
    presentar_invitacion,
    presentar_invitacion_preview,
)
from src.identidad.use_cases.generar_invitacion import GenerarInvitacionUseCase
from src.identidad.use_cases.obtener_invitacion import ObtenerInvitacionUseCase


class InvitacionesController:
    """Adapta requests HTTP a los casos de uso sobre `Invitacion` (comando y consulta)."""

    def __init__(
        self,
        generar_invitacion: GenerarInvitacionUseCase,
        obtener_invitacion: ObtenerInvitacionUseCase,
    ) -> None:
        """Recibe los casos de uso de generación y de consulta de invitación."""
        self._generar_invitacion = generar_invitacion
        self._obtener_invitacion = obtener_invitacion

    async def generar_invitacion(
        self,
        comision_id: UUID,
        docente_id: UUID,
        email_destinatario: str | None,
        solicitante_id: UUID,
    ) -> InvitacionSalida:
        """Delega la generación de la invitación en el caso de uso correspondiente."""
        invitacion, _evento = await self._generar_invitacion.execute(
            comision_id, docente_id, email_destinatario, solicitante_id
        )
        return presentar_invitacion(invitacion)

    async def obtener_invitacion(self, token: str) -> InvitacionPreviewSalida:
        """Delega la consulta de solo lectura de una invitación en el caso de uso."""
        return presentar_invitacion_preview(await self._obtener_invitacion.execute(token))
