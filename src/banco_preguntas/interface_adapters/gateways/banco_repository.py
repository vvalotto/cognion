"""Gateway SQLAlchemy que implementa `BancoRepositoryPort`."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.banco_preguntas.entities.banco import Banco
from src.banco_preguntas.entities.ports.banco_repository_port import BancoRepositoryPort
from src.banco_preguntas.frameworks.db.models import BancoModel


class SQLAlchemyBancoRepository(BancoRepositoryPort):
    """Persiste bancos usando SQLAlchemy async."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async a usar en las operaciones."""
        self._session = session

    async def guardar(self, banco: Banco) -> None:
        """Guarda un banco nuevo."""
        self._session.add(BancoModel(id=banco.id, materia_id=banco.materia_id))
        await self._session.commit()
