"""Caso de uso: consulta de solo lectura de una invitación por su token."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from src.identidad.entities.errors import InvitacionInvalida
from src.identidad.entities.ports.comision_repository_port import ComisionRepositoryPort
from src.identidad.entities.ports.invitacion_repository_port import InvitacionRepositoryPort
from src.identidad.entities.ports.materia_port import MateriaPort


@dataclass(frozen=True)
class InvitacionPreview:
    """Vista previa de una invitación vigente, sin datos sensibles (`docente_id`, email)."""

    materia: str
    horario: str


class ObtenerInvitacionUseCase:
    """Resuelve materia y horario de una invitación vigente, sin consumirla."""

    def __init__(
        self,
        invitacion_repositorio: InvitacionRepositoryPort,
        comision_repositorio: ComisionRepositoryPort,
        materia_port: MateriaPort,
    ) -> None:
        """Recibe los puertos de consulta necesarios."""
        self._invitacion_repositorio = invitacion_repositorio
        self._comision_repositorio = comision_repositorio
        self._materia_port = materia_port

    async def execute(self, token: str) -> InvitacionPreview:
        """Devuelve materia y horario de la comisión de una invitación vigente.

        Lanza `InvitacionInvalida` si el token no corresponde a ninguna invitación,
        `InvitacionVencida` o `InvitacionYaUsada` si ya no está vigente (INV-ID-01,
        INV-ID-03) — ver `Invitacion.verificar_vigente`, que no muta la invitación.
        """
        invitacion = await self._invitacion_repositorio.obtener_por_token(token)
        if invitacion is None:
            raise InvitacionInvalida(token)
        invitacion.verificar_vigente(datetime.now(UTC))

        comision = await self._comision_repositorio.obtener_por_id(invitacion.comision_id)
        assert comision is not None
        materia = await self._materia_port.obtener(comision.materia_id)
        assert materia is not None
        return InvitacionPreview(materia=materia.nombre, horario=comision.horario)
