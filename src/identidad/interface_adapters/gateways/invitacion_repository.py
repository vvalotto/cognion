"""Gateway SQLAlchemy que implementa `InvitacionRepositoryPort`."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
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
        """Guarda cambios sobre una invitación existente.

        Solo se invoca sobre invitaciones ya persistidas (ver `obtener_por_token`); si el
        registro no está, es un error del llamador, no un caso a manejar en silencio.
        """
        modelo = await self._session.get(InvitacionModel, invitacion.id)
        if modelo is None:
            raise ValueError(f"Invitación '{invitacion.id}' no existe para actualizar.")
        modelo.usada_en = invitacion.usada_en
        modelo.revocada_en = invitacion.revocada_en
        modelo.usos = invitacion.usos
        await self._session.commit()

    async def obtener_por_id(self, invitacion_id: UUID) -> Invitacion | None:
        """Busca una invitación por id, o `None` si no existe."""
        modelo = await self._session.get(InvitacionModel, invitacion_id)
        return None if modelo is None else self._a_entidad(modelo)

    async def obtener_grupal_vigente(self, comision_id: UUID, ahora: datetime) -> Invitacion | None:
        """Busca el link grupal de la comisión que no está revocado ni vencido, o `None`."""
        resultado = await self._session.execute(
            select(InvitacionModel)
            .where(
                InvitacionModel.comision_id == comision_id,
                InvitacionModel.grupal.is_(True),
                InvitacionModel.revocada_en.is_(None),
                InvitacionModel.expira_en > ahora,
            )
            .order_by(InvitacionModel.generada_en.desc())
            .limit(1)
        )
        modelo = resultado.scalar_one_or_none()
        return None if modelo is None else self._a_entidad(modelo)

    async def obtener_ultima_grupal(self, comision_id: UUID) -> Invitacion | None:
        """Busca el último link grupal generado para la comisión, o `None` si nunca hubo."""
        resultado = await self._session.execute(
            select(InvitacionModel)
            .where(InvitacionModel.comision_id == comision_id, InvitacionModel.grupal.is_(True))
            .order_by(InvitacionModel.generada_en.desc())
            .limit(1)
        )
        modelo = resultado.scalar_one_or_none()
        return None if modelo is None else self._a_entidad(modelo)

    async def reemplazar(self, anterior: Invitacion | None, nueva: Invitacion) -> None:
        """Revoca `anterior` y guarda `nueva` en una sola transacción."""
        if anterior is not None:
            modelo = await self._session.get(InvitacionModel, anterior.id)
            if modelo is not None:
                modelo.revocada_en = anterior.revocada_en
        self._session.add(self._a_model(nueva))
        await self._session.commit()

    async def incrementar_usos(self, invitacion_id: UUID) -> None:
        """Suma un uso con un `UPDATE usos = usos + 1`: seguro ante registros simultáneos."""
        await self._session.execute(
            update(InvitacionModel)
            .where(InvitacionModel.id == invitacion_id)
            .values(usos=InvitacionModel.usos + 1)
        )
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
            grupal=invitacion.grupal,
            usos=invitacion.usos,
            revocada_en=invitacion.revocada_en,
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
            grupal=modelo.grupal,
            usos=modelo.usos,
            revocada_en=modelo.revocada_en,
        )
