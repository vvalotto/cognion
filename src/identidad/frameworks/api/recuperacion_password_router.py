"""Router FastAPI de recuperación de contraseña por autoservicio (`US-ADJ-38`, `US-ADJ-39`)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.identidad.entities.errors import (
    PasswordDemasiadoCorta,
    PasswordSinComplejidadSuficiente,
    TokenRecuperacionInvalido,
    TokenRecuperacionVencido,
    TokenRecuperacionYaUsado,
)
from src.identidad.frameworks.api.schemas import (
    ConfirmarRecuperacionPasswordRequest,
    ConfirmarRecuperacionPasswordResponse,
    SolicitarRecuperacionPasswordRequest,
    SolicitarRecuperacionPasswordResponse,
)
from src.identidad.frameworks.dependencies import get_recuperacion_password_controller
from src.identidad.interface_adapters.controllers.recuperacion_password_controller import (
    RecuperacionPasswordController,
)

router = APIRouter(prefix="/identidad", tags=["identidad"])


@router.post(
    "/recuperar-password/solicitar",
    response_model=SolicitarRecuperacionPasswordResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def solicitar_recuperacion_password(
    body: SolicitarRecuperacionPasswordRequest,
    controller: RecuperacionPasswordController = Depends(get_recuperacion_password_controller),
) -> SolicitarRecuperacionPasswordResponse:
    """Solicita la recuperación de contraseña; endpoint público, sin JWT.

    Responde siempre 202 con el mismo mensaje genérico, exista o no una cuenta con ese email
    (INV-ID-17) — no hay ninguna excepción de dominio que mapear a un status distinto.
    """
    await controller.solicitar(body.email)
    return SolicitarRecuperacionPasswordResponse()


@router.post(
    "/recuperar-password/confirmar",
    response_model=ConfirmarRecuperacionPasswordResponse,
    status_code=status.HTTP_200_OK,
)
async def confirmar_recuperacion_password(
    body: ConfirmarRecuperacionPasswordRequest,
    controller: RecuperacionPasswordController = Depends(get_recuperacion_password_controller),
) -> ConfirmarRecuperacionPasswordResponse:
    """Canjea un token de recuperación por una contraseña nueva; endpoint público, sin JWT.

    Responde 422 si el token no es válido (inexistente, vencido o ya usado — mismo status y
    criterio que `InvitacionInvalida`/`InvitacionVencida`/`InvitacionYaUsada` en
    `registro_router.py`) o si `password_nueva` no cumple INV-ID-11 ampliada. No desbloquea la
    cuenta ni resetea sus contadores de intentos fallidos.
    """
    try:
        await controller.confirmar(body.token, body.password_nueva)
    except (
        TokenRecuperacionInvalido,
        TokenRecuperacionVencido,
        TokenRecuperacionYaUsado,
        PasswordDemasiadoCorta,
        PasswordSinComplejidadSuficiente,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    return ConfirmarRecuperacionPasswordResponse()
