"""Caso de uso: generación de un link de invitación grupal para una comisión (`US-ADJ-67`)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from src.identidad.entities.eventos import InvitacionGrupalGenerada
from src.identidad.entities.invitacion import DURACION_GRUPAL_POR_DEFECTO_MINUTOS, Invitacion
from src.identidad.entities.ports.comision_repository_port import ComisionRepositoryPort
from src.identidad.entities.ports.invitacion_repository_port import InvitacionRepositoryPort
from src.identidad.use_cases.autorizacion_comision import exigir_docente_asignado


class GenerarInvitacionGrupalUseCase:
    """Genera el link que toda la comisión puede usar y desactiva el grupal anterior, si lo hay."""

    def __init__(
        self,
        comision_repositorio: ComisionRepositoryPort,
        invitacion_repositorio: InvitacionRepositoryPort,
    ) -> None:
        """Recibe los repositorios de comisiones e invitaciones."""
        self._comision_repositorio = comision_repositorio
        self._invitacion_repositorio = invitacion_repositorio

    async def execute(
        self,
        comision_id: UUID,
        solicitante_id: UUID,
        duracion_minutos: int = DURACION_GRUPAL_POR_DEFECTO_MINUTOS,
    ) -> tuple[Invitacion, InvitacionGrupalGenerada]:
        """Crea el link grupal y revoca el vigente de la comisión en la misma operación.

        Lanza `ComisionNoExiste` si la comisión no existe, `ComisionNoAutorizada` si quien lo pide
        (`solicitante_id`, del JWT) no está asignado a ella, y `DuracionInvitacionInvalida` si la
        duración no es 15, 60 o 1440 minutos. Hay un solo link grupal vigente por comisión.
        """
        await exigir_docente_asignado(self._comision_repositorio, comision_id, solicitante_id)

        nueva = Invitacion.crear_grupal(comision_id, solicitante_id, duracion_minutos)
        ahora = datetime.now(UTC)
        anterior = await self._invitacion_repositorio.obtener_grupal_vigente(comision_id, ahora)
        if anterior is not None:
            anterior.revocar(ahora)
        await self._invitacion_repositorio.reemplazar(anterior, nueva)

        evento = InvitacionGrupalGenerada(
            invitacion_id=nueva.id,
            comision_id=comision_id,
            docente_id=solicitante_id,
            expira_en=nueva.expira_en,
        )
        return nueva, evento
