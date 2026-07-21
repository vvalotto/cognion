from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID


def _ahora() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class UsuarioCreado:
    usuario_id: UUID
    email: str
    tipo_perfil: str
    ocurrido_en: datetime = field(default_factory=_ahora)


@dataclass(frozen=True)
class ComisionCreada:
    comision_id: UUID
    materia: str
    ocurrido_en: datetime = field(default_factory=_ahora)


@dataclass(frozen=True)
class DocenteAsignado:
    comision_id: UUID
    docente_id: UUID
    ocurrido_en: datetime = field(default_factory=_ahora)
