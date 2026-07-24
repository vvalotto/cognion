"""Implementación de `JWTIssuerPort` con PyJWT (ADR-007, ADR-013)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from src.identidad.entities.errors import JWTExpirado, JWTInvalido
from src.identidad.entities.jwt import JWT, JWTPayload
from src.identidad.entities.ports.jwt_issuer_port import JWTIssuerPort
from src.identidad.entities.usuario import TipoPerfil
from src.settings import settings


class PyJWTIssuer(JWTIssuerPort):
    """Emite y verifica tokens de sesión firmados con `settings.secret_key` (exp. 60 min)."""

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

    def verificar(self, token: str) -> JWTPayload:
        """Decodifica `token`; levanta `JWTExpirado`/`JWTInvalido` si no verifica (`US-1.1.5`)."""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        except jwt.ExpiredSignatureError as exc:
            raise JWTExpirado() from exc
        except jwt.InvalidTokenError as exc:
            raise JWTInvalido() from exc

        try:
            return JWTPayload(usuario_id=UUID(payload["sub"]), rol=TipoPerfil(payload["rol"]))
        except (KeyError, ValueError) as exc:
            raise JWTInvalido() from exc
