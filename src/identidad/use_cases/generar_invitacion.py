"""Caso de uso: generación de una invitación para una comisión."""

from __future__ import annotations

from uuid import UUID

from src.identidad.entities.comision import Comision
from src.identidad.entities.errors import ComisionNoExiste, DocenteNoAsignadoAComision
from src.identidad.entities.eventos import InvitacionGenerada
from src.identidad.entities.invitacion import Invitacion
from src.identidad.entities.ports.comision_repository_port import ComisionRepositoryPort
from src.identidad.entities.ports.invitacion_repository_port import InvitacionRepositoryPort
from src.identidad.entities.ports.notificador_port import NotificadorPort


class GenerarInvitacionUseCase:
    """Genera una invitación para que un Docente asignado la envíe a un Estudiante."""

    def __init__(
        self,
        comision_repositorio: ComisionRepositoryPort,
        invitacion_repositorio: InvitacionRepositoryPort,
        notificador: NotificadorPort,
    ) -> None:
        """Recibe los repositorios de comisiones e invitaciones y el notificador a usar."""
        self._comision_repositorio = comision_repositorio
        self._invitacion_repositorio = invitacion_repositorio
        self._notificador = notificador

    async def execute(
        self, comision_id: UUID, docente_id: UUID, email_destinatario: str
    ) -> tuple[Invitacion, InvitacionGenerada]:
        """Genera y persiste la invitación, envía el email y devuelve el evento emitido.

        Lanza `ComisionNoExiste` si la comisión no existe, y `DocenteNoAsignadoAComision`
        si el docente no está en `Comision.docentes_asignados` (INV-ID-08).
        """
        comision = await self._comision_repositorio.obtener_por_id(comision_id)
        if comision is None:
            raise ComisionNoExiste(comision_id)

        self._validar_docente_asignado(comision, docente_id)

        invitacion = Invitacion.crear(comision_id, docente_id)
        await self._invitacion_repositorio.guardar(invitacion)
        await self._notificador.enviar_invitacion(email_destinatario, invitacion.token)

        evento = InvitacionGenerada(
            invitacion_id=invitacion.id,
            comision_id=comision_id,
            docente_id=docente_id,
            token=invitacion.token,
        )
        return invitacion, evento

    @staticmethod
    def _validar_docente_asignado(comision: Comision, docente_id: UUID) -> None:
        """Lanza `DocenteNoAsignadoAComision` si el docente no está asignado a la comisión."""
        if docente_id not in comision.docentes_asignados:
            raise DocenteNoAsignadoAComision(docente_id, comision.id)
