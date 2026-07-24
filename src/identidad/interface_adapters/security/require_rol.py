"""Dependency FastAPI que restringe el acceso a una lista de roles permitidos (RF-02)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Depends, HTTPException, status

from src.identidad.entities.jwt import JWTPayload
from src.identidad.entities.usuario import TipoPerfil


def require_rol(
    roles_permitidos: list[TipoPerfil],
    get_current_user: Callable[..., Awaitable[JWTPayload]],
) -> Callable[[JWTPayload], Awaitable[JWTPayload]]:
    """Arma una dependency que exige `usuario.rol` dentro de `roles_permitidos`.

    Compone sobre `get_current_user` (recibido como parámetro, no importado) — un `Usuario`
    sin JWT válido nunca llega a la verificación de rol: `get_current_user` ya respondió 401.
    """

    async def _verificar_rol(
        usuario: JWTPayload = Depends(get_current_user),
    ) -> JWTPayload:
        """Verifica el rol del `Usuario` autenticado; responde 403 si no está permitido."""
        if usuario.rol not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El rol del usuario no tiene acceso a este recurso.",
            )
        return usuario

    return _verificar_rol
