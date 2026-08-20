"""Eventos de dominio emitidos por el BC Identidad."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from src.shared.entities.tipo_perfil import TipoPerfil


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
    materia_id: UUID
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


@dataclass(frozen=True)
class CuentaBloqueada:
    """Una cuenta llegó a 3 intentos fallidos consecutivos y se bloqueó (RF-19).

    Puede ser el flujo de login o el de cambio de contraseña (INV-ID-10).
    """

    usuario_id: UUID
    ocurrido_en: datetime = field(default_factory=_ahora)


@dataclass(frozen=True)
class PasswordReseteada:
    """Un Administrador reseteó la contraseña de una cuenta (RF-03, `US-2.2.4`)."""

    usuario_id: UUID
    administrador_id: UUID
    ocurrido_en: datetime = field(default_factory=_ahora)


@dataclass(frozen=True)
class CuentaDesbloqueada:
    """Una cuenta bloqueada volvió a estar activa tras un reseteo de contraseña.

    Se emite junto con `PasswordReseteada` solo si la cuenta estaba `bloqueada = true`
    (`US-2.2.4`) — no existe un comando `DesbloquearCuenta` separado.
    """

    usuario_id: UUID
    ocurrido_en: datetime = field(default_factory=_ahora)
