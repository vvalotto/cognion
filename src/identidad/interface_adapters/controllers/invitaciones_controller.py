"""Controller de la API para operaciones sobre invitaciones."""

from __future__ import annotations

from uuid import UUID

from src.identidad.entities.eventos import InvitacionGenerada
from src.identidad.entities.invitacion import Invitacion
from src.identidad.use_cases.generar_invitacion import GenerarInvitacionUseCase


class InvitacionesController:
    """Adapta requests HTTP al caso de uso de generación de invitaciones."""

    def __init__(self, generar_invitacion: GenerarInvitacionUseCase) -> None:
        """Recibe el caso de uso de generación de invitación."""
        self._generar_invitacion = generar_invitacion

    async def generar_invitacion(
        self, comision_id: UUID, docente_id: UUID, email_destinatario: str
    ) -> tuple[Invitacion, InvitacionGenerada]:
        """Delega la generación de la invitación en el caso de uso correspondiente."""
        return await self._generar_invitacion.execute(comision_id, docente_id, email_destinatario)
