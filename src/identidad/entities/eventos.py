"""Eventos de dominio emitidos por el BC Identidad."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID


def _ahora() -> datetime:
    """Devuelve el instante actual en UTC."""
    return datetime.now(UTC)


@dataclass(frozen=True)
class UsuarioCreado:
    """Se registró un nuevo usuario."""

    usuario_id: UUID
    email: str
    tipo_perfil: str
    ocurrido_en: datetime = field(default_factory=_ahora)


@dataclass(frozen=True)
class ComisionCreada:
    """Se creó una nueva comisión."""

    comision_id: UUID
    materia: str
    ocurrido_en: datetime = field(default_factory=_ahora)


@dataclass(frozen=True)
class DocenteAsignado:
    """Se asignó un docente a una comisión."""

    comision_id: UUID
    docente_id: UUID
    ocurrido_en: datetime = field(default_factory=_ahora)
