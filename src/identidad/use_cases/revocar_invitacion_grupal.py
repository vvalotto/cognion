"""Caso de uso: desactivación de un link de invitación grupal (`US-ADJ-67`)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from src.identidad.entities.errors import InvitacionInvalida
from src.identidad.entities.eventos import InvitacionGrupalRevocada
from src.identidad.entities.ports.comision_repository_port import ComisionRepositoryPort
from src.identidad.entities.ports.invitacion_repository_port import InvitacionRepositoryPort
from src.identidad.use_cases.autorizacion_comision import exigir_docente_asignado


class RevocarInvitacionGrupalUseCase:
    """Desactiva el link grupal de una comisión; quienes ya se registraron no se ven afectados."""

    def __init__(
        self,
        comision_repositorio: ComisionRepositoryPort,
        invitacion_repositorio: InvitacionRepositoryPort,
    ) -> None:
        """Recibe los repositorios de comisiones e invitaciones."""
        self._comision_repositorio = comision_repositorio
        self._invitacion_repositorio = invitacion_repositorio

    async def execute(
        self, comision_id: UUID, invitacion_id: UUID, solicitante_id: UUID
    ) -> InvitacionGrupalRevocada | None:
        """Revoca el link si está vigente; devuelve el evento, o `None` si ya no lo estaba.

        Es idempotente: desactivar un link ya revocado o vencido no falla ni cambia nada. Lanza
        `ComisionNoExiste`, `ComisionNoAutorizada` (el Docente no está asignado a la comisión) o
        `InvitacionInvalida` si la invitación no existe, no es de esa comisión o no es grupal.
        """
        await exigir_docente_asignado(self._comision_repositorio, comision_id, solicitante_id)

        invitacion = await self._invitacion_repositorio.obtener_por_id(invitacion_id)
        if invitacion is None or invitacion.comision_id != comision_id or not invitacion.grupal:
            raise InvitacionInvalida(str(invitacion_id))

        if not invitacion.revocar(datetime.now(UTC)):
            return None
        await self._invitacion_repositorio.actualizar(invitacion)
        return InvitacionGrupalRevocada(invitacion_id=invitacion.id, comision_id=comision_id)
