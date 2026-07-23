"""Gateway SQLAlchemy que implementa `InvitacionRepositoryPort`."""

from __future__ import annotations

from sqlalchemy import select
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
        self._session.add(self._a_model(invitacion))
        await self._session.commit()

    async def obtener_por_token(self, token: str) -> Invitacion | None:
        """Busca una invitación por token, o `None` si no existe."""
        resultado = await self._session.execute(
            select(InvitacionModel).where(InvitacionModel.token == token)
        )
        modelo = resultado.scalar_one_or_none()
        return None if modelo is None else self._a_entidad(modelo)

    async def actualizar(self, invitacion: Invitacion) -> None:
        """Guarda cambios sobre una invitación existente."""
        modelo = await self._session.get(InvitacionModel, invitacion.id)
        modelo.usada_en = invitacion.usada_en
        await self._session.commit()

    @staticmethod
    def _a_model(invitacion: Invitacion) -> InvitacionModel:
        """Construye el modelo ORM correspondiente a una `Invitacion`."""
        return InvitacionModel(
            id=invitacion.id,
            comision_id=invitacion.comision_id,
            docente_id=invitacion.docente_id,
            token=invitacion.token,
            generada_en=invitacion.generada_en,
            expira_en=invitacion.expira_en,
            usada_en=invitacion.usada_en,
        )

    @staticmethod
    def _a_entidad(modelo: InvitacionModel) -> Invitacion:
        """Reconstruye una `Invitacion` a partir de su modelo ORM."""
        return Invitacion(
            id=modelo.id,
            comision_id=modelo.comision_id,
            docente_id=modelo.docente_id,
            token=modelo.token,
            generada_en=modelo.generada_en,
            expira_en=modelo.expira_en,
            usada_en=modelo.usada_en,
        )
