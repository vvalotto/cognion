"""Gateway SQLAlchemy que implementa `InvitacionRepositoryPort`."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.identidad.entities.invitacion import Invitacion
from src.identidad.entities.ports.invitacion_repository_port import InvitacionRepositoryPort
from src.identidad.frameworks.db.models import InvitacionModel


class SQLAlchemyInvitacionRepository(InvitacionRepositoryPort):
    """Persiste invitaciones usando SQLAlchemy async."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async a usar en las operaciones."""
        self._session = session

    async def guardar(self, invitacion: Invitacion) -> None:
        """Guarda una invitación nueva."""
        self._session.add(
            InvitacionModel(
                id=invitacion.id,
                comision_id=invitacion.comision_id,
                docente_id=invitacion.docente_id,
                token=invitacion.token,
                generada_en=invitacion.generada_en,
                expira_en=invitacion.expira_en,
                usada_en=invitacion.usada_en,
            )
        )
        await self._session.commit()
