"""Implementación de `JWTIssuerPort` con PyJWT (ADR-007, ADR-013)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from src.identidad.entities.jwt import JWT
from src.identidad.entities.ports.jwt_issuer_port import JWTIssuerPort
from src.identidad.entities.usuario import TipoPerfil
from src.settings import settings


class PyJWTIssuer(JWTIssuerPort):
    """Emite tokens de sesión firmados con `settings.secret_key`, expiración de 60 minutos."""

    def emitir(self, usuario_id: UUID, rol: TipoPerfil) -> JWT:
        """Firma un JWT con claims `sub` y `rol`, `exp` a `access_token_expire_minutes`."""
        ahora = datetime.now(UTC)
        expira_en = ahora + timedelta(minutes=settings.access_token_expire_minutes)
        payload = {
            "sub": str(usuario_id),
            "rol": rol.value,
            "exp": expira_en,
        }
        token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
        return JWT(token=token, rol=rol, expira_en=expira_en)
