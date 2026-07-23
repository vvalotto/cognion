"""Eventos de dominio emitidos por el BC Identidad."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from src.identidad.entities.usuario import TipoPerfil


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


@dataclass(frozen=True)
class InvitacionGenerada:
    """Un Docente generó una invitación para su Comisión."""

    invitacion_id: UUID
    comision_id: UUID
    docente_id: UUID
    token: str
    ocurrido_en: datetime = field(default_factory=_ahora)


@dataclass(frozen=True)
class InvitacionAceptada:
    """Un Estudiante aceptó una invitación y quedó asignado a la comisión."""

    invitacion_id: UUID
    comision_id: UUID
    usuario_id: UUID
    ocurrido_en: datetime = field(default_factory=_ahora)


@dataclass(frozen=True)
class UsuarioRegistrado:
    """Un Estudiante completó su registro vía invitación (RF-01)."""

    usuario_id: UUID
    email: str
    comision_id: UUID
    ocurrido_en: datetime = field(default_factory=_ahora)


@dataclass(frozen=True)
class SesionIniciada:
    """Un Usuario se autenticó exitosamente y recibió un JWT con su rol (RF-02)."""

    usuario_id: UUID
    rol: TipoPerfil
    ocurrido_en: datetime = field(default_factory=_ahora)
