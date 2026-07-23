"""Router FastAPI de autenticación de Usuarios."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.identidad.entities.errors import CredencialesInvalidas
from src.identidad.frameworks.api.schemas import LoginRequest, LoginResponse
from src.identidad.frameworks.dependencies import get_auth_controller
from src.identidad.interface_adapters.controllers.auth_controller import AuthController

router = APIRouter(prefix="/identidad", tags=["identidad"])


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    body: LoginRequest,
    controller: AuthController = Depends(get_auth_controller),
) -> LoginResponse:
    """Autentica un Usuario y emite su JWT; responde 401 genérico ante credenciales inválidas.

    El mensaje de error no distingue si el email existe o no (`US-1.1.4`).
    """
    try:
        jwt_vo, _evento = await controller.iniciar_sesion(body.email, body.password)
    except CredencialesInvalidas as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return LoginResponse(
        access_token=jwt_vo.token,
        rol=jwt_vo.rol,
        expira_en=jwt_vo.expira_en,
    )
