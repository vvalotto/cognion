"""Router FastAPI de autoregistro de cuentas sin invitación (`US-ADJ-41`)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.identidad.entities.errors import (
    EmailYaRegistrado,
    PasswordDemasiadoCorta,
    PasswordSinComplejidadSuficiente,
)
from src.identidad.frameworks.api.schemas import AutoregistrarDocenteRequest, AutoregistroResponse
from src.identidad.frameworks.dependencies import get_autoregistro_controller
from src.identidad.interface_adapters.controllers.autoregistro_controller import (
    AutoregistroController,
)

router = APIRouter(prefix="/identidad/autoregistro", tags=["identidad"])


@router.post("/docente", response_model=AutoregistroResponse, status_code=status.HTTP_201_CREATED)
async def autoregistrar_docente(
    body: AutoregistrarDocenteRequest,
    controller: AutoregistroController = Depends(get_autoregistro_controller),
) -> AutoregistroResponse:
    """Crea una cuenta de Docente activa de inmediato; endpoint público, sin JWT.

    Responde 409 si el email ya está registrado, o 422 si `password` no cumple INV-ID-11
    (ampliada, `US-ADJ-36`).
    """
    try:
        usuario, _evento = await controller.autoregistrar_docente(
            body.nombre, body.email, body.password
        )
    except EmailYaRegistrado as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except (PasswordDemasiadoCorta, PasswordSinComplejidadSuficiente) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    return AutoregistroResponse(
        id=usuario.id,
        nombre=usuario.nombre,
        email=usuario.email,
        tipo_perfil=usuario.tipo_perfil.value,
    )
