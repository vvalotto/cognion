"""Dependency FastAPI que resuelve el `Usuario` autenticado a partir del JWT recibido."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.identidad.entities.errors import JWTExpirado, JWTInvalido
from src.identidad.entities.jwt import JWTPayload
from src.identidad.entities.ports.jwt_issuer_port import JWTIssuerPort

_bearer_scheme = HTTPBearer(auto_error=False)


def build_get_current_user(
    jwt_issuer: JWTIssuerPort,
) -> Callable[[HTTPAuthorizationCredentials | None], Awaitable[JWTPayload]]:
    """Arma la dependency `get_current_user` ligada al `JWTIssuerPort` concreto recibido.

    `jwt_issuer` se recibe como parámetro (la abstracción, no `PyJWTIssuer`) para que este
    módulo de `interface_adapters` no importe `frameworks` — el wiring con la implementación
    concreta ocurre en el composition root (`frameworks/dependencies.py`).
    """

    async def get_current_user(
        credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    ) -> JWTPayload:
        """Decodifica el JWT del header `Authorization`; responde 401 si falta o no es válido."""
        if credentials is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado.")
        try:
            return jwt_issuer.verificar(credentials.credentials)
        except (JWTInvalido, JWTExpirado) as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return get_current_user
