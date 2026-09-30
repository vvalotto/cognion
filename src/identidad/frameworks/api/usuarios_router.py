"""Router FastAPI de operaciones sobre usuarios."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.identidad.entities.errors import (
    EmailYaRegistrado,
    PasswordDemasiadoCorta,
    PasswordSinComplejidadSuficiente,
)
from src.identidad.frameworks.api.schemas import CrearUsuarioRequest, UsuarioResponse
from src.identidad.frameworks.dependencies import get_usuarios_controller, require_administrador
from src.identidad.interface_adapters.controllers.usuarios_controller import UsuariosController

router = APIRouter(prefix="/usuarios", tags=["identidad"])


@router.post(
    "",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_administrador)],
)
async def crear_usuario(
    body: CrearUsuarioRequest,
    controller: UsuariosController = Depends(get_usuarios_controller),
) -> UsuarioResponse:
    """Crea un usuario nuevo.

    Responde 409 si el email ya está registrado, 422 si `password` no cumple INV-ID-11
    (`US-ADJ-36`).
    """
    try:
        usuario, _evento = await controller.crear_usuario(
            body.nombre, body.email, body.password, body.perfil
        )
    except EmailYaRegistrado as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except (PasswordDemasiadoCorta, PasswordSinComplejidadSuficiente) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    return UsuarioResponse(
        id=usuario.id, nombre=usuario.nombre, email=usuario.email, perfil=usuario.tipo_perfil
    )
