"""Gateway SQLAlchemy que implementa `NombreUsuarioQueryPort` (`US-9.4.2`)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.identidad.entities.ports.nombre_usuario_query_port import NombreUsuarioQueryPort
from src.identidad.frameworks.db.models import UsuarioModel


class SQLAlchemyNombreUsuarioQueryRepository(NombreUsuarioQueryPort):
    """Resuelve nombres de usuario por lote con una sola consulta."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async a usar en la consulta."""
        self._session = session

    async def obtener_nombres(self, ids: list[UUID]) -> dict[UUID, str]:
        """Resuelve `nombre` para `ids` con un único `SELECT ... WHERE id IN (...)`."""
        if not ids:
            return {}
        resultado = await self._session.execute(
            select(UsuarioModel.id, UsuarioModel.nombre).where(UsuarioModel.id.in_(ids))
        )
        return {fila.id: fila.nombre for fila in resultado}
