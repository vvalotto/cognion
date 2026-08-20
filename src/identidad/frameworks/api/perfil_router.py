"""Router FastAPI de acciones self-service sobre la propia cuenta (RF-19)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.identidad.entities.errors import (
    CuentaBloqueadaError,
    PasswordActualIncorrecta,
    PasswordDemasiadoCorta,
)
from src.identidad.frameworks.api.schemas import CambiarPasswordRequest
from src.identidad.frameworks.dependencies import get_current_user, get_perfil_controller
from src.identidad.interface_adapters.controllers.perfil_controller import PerfilController
from src.shared.entities.jwt import JWTPayload

router = APIRouter(prefix="/usuarios/me", tags=["identidad"])


@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
async def cambiar_password(
    body: CambiarPasswordRequest,
    usuario: JWTPayload = Depends(get_current_user),
    controller: PerfilController = Depends(get_perfil_controller),
) -> None:
    """Cambia la contraseña del Usuario autenticado; cualquier rol puede usarlo.

    Responde 401 si `password_actual` no verifica, 403 si la cuenta ya está bloqueada, 422 si
    `password_nueva` no cumple INV-ID-11.
    """
    try:
        await controller.cambiar_password(
            usuario.usuario_id, body.password_actual, body.password_nueva
        )
    except CuentaBloqueadaError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except PasswordActualIncorrecta as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except PasswordDemasiadoCorta as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
