"""Gateway SQLAlchemy que implementa `TokenRecuperacionPasswordRepositoryPort`."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.identidad.entities.ports.token_recuperacion_password_repository_port import (
    TokenRecuperacionPasswordRepositoryPort,
)
from src.identidad.entities.token_recuperacion_password import TokenRecuperacionPassword
from src.identidad.frameworks.db.models import TokenRecuperacionPasswordModel


class SQLAlchemyTokenRecuperacionPasswordRepository(TokenRecuperacionPasswordRepositoryPort):
    """Persiste tokens de recuperación de contraseña usando SQLAlchemy async."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async a usar en las operaciones."""
        self._session = session

    async def guardar(self, token: TokenRecuperacionPassword) -> None:
        """Guarda un token nuevo."""
        self._session.add(self._a_model(token))
        await self._session.commit()

    async def obtener_por_token(self, token: str) -> TokenRecuperacionPassword | None:
        """Busca un token de recuperación por su valor, o `None` si no existe."""
        resultado = await self._session.execute(
            select(TokenRecuperacionPasswordModel).where(
                TokenRecuperacionPasswordModel.token == token
            )
        )
        modelo = resultado.scalar_one_or_none()
        return None if modelo is None else self._a_entidad(modelo)

    async def invalidar_activos_de(self, usuario_id: UUID, ahora: datetime) -> None:
        """Marca `usado_en = ahora` en cualquier token sin usar de `usuario_id` (INV-ID-12)."""
        await self._session.execute(
            update(TokenRecuperacionPasswordModel)
            .where(
                TokenRecuperacionPasswordModel.usuario_id == usuario_id,
                TokenRecuperacionPasswordModel.usado_en.is_(None),
            )
            .values(usado_en=ahora)
        )
        await self._session.commit()

    async def actualizar(self, token: TokenRecuperacionPassword) -> None:
        """Guarda cambios sobre un token existente.

        Solo se invoca sobre tokens ya persistidos (ver `obtener_por_token`); si el registro
        no está, es un error del llamador, no un caso a manejar en silencio.
        """
        modelo = await self._session.get(TokenRecuperacionPasswordModel, token.id)
        if modelo is None:
            raise ValueError(f"TokenRecuperacionPassword '{token.id}' no existe para actualizar.")
        modelo.usado_en = token.usado_en
        await self._session.commit()

    async def eliminar_de(self, usuario_id: UUID) -> None:
        """Borra físicamente todos los tokens de `usuario_id`."""
        await self._session.execute(
            delete(TokenRecuperacionPasswordModel).where(
                TokenRecuperacionPasswordModel.usuario_id == usuario_id
            )
        )
        await self._session.commit()

    @staticmethod
    def _a_model(token: TokenRecuperacionPassword) -> TokenRecuperacionPasswordModel:
        """Construye el modelo ORM correspondiente a un `TokenRecuperacionPassword`."""
        return TokenRecuperacionPasswordModel(
            id=token.id,
            usuario_id=token.usuario_id,
            token=token.token,
            generado_en=token.generado_en,
            expira_en=token.expira_en,
            usado_en=token.usado_en,
        )

    @staticmethod
    def _a_entidad(modelo: TokenRecuperacionPasswordModel) -> TokenRecuperacionPassword:
        """Reconstruye un `TokenRecuperacionPassword` a partir de su modelo ORM."""
        return TokenRecuperacionPassword(
            id=modelo.id,
            usuario_id=modelo.usuario_id,
            token=modelo.token,
            generado_en=modelo.generado_en,
            expira_en=modelo.expira_en,
            usado_en=modelo.usado_en,
        )
