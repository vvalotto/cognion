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

    Responde 401 si `password_actual` no verifica: `detail.intentos_restantes` cuenta los
    fallos que quedan antes del bloqueo (INV-ID-10), o `detail.bloqueada = true` si este
    intento fue el 3er fallo consecutivo y acaba de bloquear la cuenta. Responde 403 con
    `detail.bloqueada = true` si la cuenta ya estaba bloqueada antes de este intento
    (`CuentaBloqueadaError`, sin llegar a verificar `password_actual`). Responde 422 si
    `password_nueva` no cumple INV-ID-11 (`US-2.2.8`).
    """
    try:
        await controller.cambiar_password(
            usuario.usuario_id, body.password_actual, body.password_nueva
        )
    except CuentaBloqueadaError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"mensaje": str(exc), "bloqueada": True},
        ) from exc
    except PasswordActualIncorrecta as exc:
        detail: dict[str, object] = {"mensaje": str(exc)}
        if exc.evento_cuenta_bloqueada is not None:
            detail["bloqueada"] = True
        else:
            detail["intentos_restantes"] = exc.intentos_restantes
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail) from exc
    except PasswordDemasiadoCorta as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"mensaje": str(exc)},
        ) from exc
