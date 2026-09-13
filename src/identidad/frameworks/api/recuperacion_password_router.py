"""Router FastAPI de recuperación de contraseña por autoservicio (`US-ADJ-38`)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from src.identidad.frameworks.api.schemas import (
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
