"""Router FastAPI de registro de Estudiantes vía invitación."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.identidad.entities.errors import EmailYaRegistrado, InvitacionNoValida
from src.identidad.frameworks.api.schemas import RegistrarEstudianteRequest, RegistroResponse
from src.identidad.frameworks.dependencies import get_registro_controller
from src.identidad.interface_adapters.controllers.registro_controller import RegistroController

router = APIRouter(prefix="/identidad", tags=["identidad"])


@router.post("/registro", response_model=RegistroResponse, status_code=status.HTTP_201_CREATED)
async def registrar_estudiante(
    body: RegistrarEstudianteRequest,
    controller: RegistroController = Depends(get_registro_controller),
) -> RegistroResponse:
    """Registra un Estudiante vía invitación; endpoint público, sin JWT (aún no autenticado).

    Responde 409 si el email ya está registrado, 422 si la invitación no es válida.
    """
    try:
        usuario, _evento_invitacion, _evento_usuario = await controller.registrar_estudiante(
            body.token, body.nombre, body.email, body.password
        )
    except EmailYaRegistrado as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except InvitacionNoValida as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    return RegistroResponse(
        id=usuario.id,
        nombre=usuario.nombre,
        email=usuario.email,
        comision_id=usuario.perfil.comision_id,
    )
