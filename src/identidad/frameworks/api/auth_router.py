"""Router FastAPI de autenticación de Usuarios."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from src.identidad.frameworks.api.schemas import LoginRequest, LoginResponse
from src.identidad.frameworks.dependencies import get_auth_controller
from src.identidad.interface_adapters.controllers.auth_controller import AuthController
from src.identidad.interface_adapters.presenters.identidad_presenter import (
    LoginSalida,
)

router = APIRouter(prefix="/identidad", tags=["identidad"])


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    body: LoginRequest,
    controller: AuthController = Depends(get_auth_controller),
) -> LoginSalida:
    """Autentica un Usuario y emite su JWT; responde 401 genérico ante credenciales inválidas.

    El mensaje de error no distingue si el email existe o no (`US-1.1.4`), salvo en el 2.º fallo
    consecutivo de una cuenta existente: ahí el `detail` es un objeto con `mensaje` e
    `intentos_restantes = 1`, para avisar que el próximo intento la bloquea (`US-ADJ-69`).
    Responde 403 si la
    cuenta está bloqueada por 3 intentos fallidos consecutivos (`US-2.2.1`), con el `detail` en
    texto plano. Responde 403 también si la cuenta está deshabilitada (`US-ADJ-59`), pero con un
    `detail` estructurado `{"codigo": "cuenta_deshabilitada", "mensaje": ...}` para que el
    frontend distinga los dos casos sin interpretar el texto. Responde 403
    `cuenta_bloqueada_temporal` (con `reintentar_en_segundos`) si es el último Administrador
    operativo bloqueado (`US-ADJ-60`).
    """
    return await controller.iniciar_sesion(body.email, body.password)
