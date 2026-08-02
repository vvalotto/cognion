"""Eventos de dominio emitidos por el BC Banco de Preguntas."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID


def _ahora() -> datetime:
    """Devuelve el instante actual en UTC."""
    return datetime.now(UTC)


@dataclass(frozen=True)
class MateriaCreada:
    """Se dio de alta una materia nueva."""

    materia_id: UUID
    nombre: str
    ocurrido_en: datetime = field(default_factory=_ahora)


@dataclass(frozen=True)
class BancoCreado:
    """Se creó el banco de preguntas de una materia."""

    banco_id: UUID
    materia_id: UUID
    ocurrido_en: datetime = field(default_factory=_ahora)
