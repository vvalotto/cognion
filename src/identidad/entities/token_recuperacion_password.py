"""Token de recuperación de contraseña por autoservicio.

`US-ADJ-38`, `BC-identidad-modelo.md` §13.3.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

EXPIRACION_HORAS = 1


@dataclass
class TokenRecuperacionPassword:
    """Token único, de un solo uso, para que un `Usuario` recupere el acceso a su cuenta."""

    id: UUID
    usuario_id: UUID
    token: str
    generado_en: datetime
    expira_en: datetime
    usado_en: datetime | None = None

    @staticmethod
    def crear(usuario_id: UUID) -> TokenRecuperacionPassword:
        """Crea un `TokenRecuperacionPassword` con expiración a 1 hora (INV-ID-13)."""
        generado_en = datetime.now(UTC)
        return TokenRecuperacionPassword(
            id=uuid4(),
            usuario_id=usuario_id,
            token=secrets.token_urlsafe(32),
            generado_en=generado_en,
            expira_en=generado_en + timedelta(hours=EXPIRACION_HORAS),
        )

    def invalidar(self, ahora: datetime) -> None:
        """Marca el token como usado, sin importar si ya lo estaba.

        Mismo mecanismo tanto para invalidar un token activo previo ante una nueva
        solicitud (INV-ID-12) como para marcarlo usado tras un canje exitoso (`US-ADJ-39`) —
        en ambos casos el efecto es idéntico: el token deja de poder canjearse.
        """
        self.usado_en = ahora
