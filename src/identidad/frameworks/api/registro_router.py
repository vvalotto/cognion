"""Router FastAPI de registro de Estudiantes vía invitación."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.identidad.entities.errors import (
    EmailYaRegistrado,
    InvitacionInvalida,
    InvitacionVencida,
    InvitacionYaUsada,
    PasswordDemasiadoCorta,
    PasswordSinComplejidadSuficiente,
)
from src.identidad.entities.usuario import Estudiante
from src.identidad.frameworks.api.schemas import (
    InvitacionPreviewResponse,
    RegistrarEstudianteRequest,
    RegistroResponse,
)
from src.identidad.frameworks.dependencies import (
    get_invitaciones_controller,
    get_registro_controller,
)
from src.identidad.interface_adapters.controllers.invitaciones_controller import (
    InvitacionesController,
)
from src.identidad.interface_adapters.controllers.registro_controller import RegistroController

router = APIRouter(prefix="/identidad", tags=["identidad"])


@router.get("/invitaciones/{token}", response_model=InvitacionPreviewResponse)
async def obtener_invitacion(
    token: str,
    controller: InvitacionesController = Depends(get_invitaciones_controller),
) -> InvitacionPreviewResponse:
    """Vista previa de una invitación por token, sin consumirla; endpoint público, sin JWT.

    Responde 404 si el token no corresponde a ninguna invitación, o 422 si ya venció o ya
    fue usada — a diferencia de `POST /registro`, aquí sí se distingue el motivo porque es
    una consulta anónima por token, sin riesgo de enumerar invitaciones ajenas (`US-ADJ-08`).
    """
    try:
        preview = await controller.obtener_invitacion(token)
    except InvitacionInvalida as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (InvitacionVencida, InvitacionYaUsada) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    return InvitacionPreviewResponse(materia=preview.materia, horario=preview.horario)


@router.post("/registro", response_model=RegistroResponse, status_code=status.HTTP_201_CREATED)
async def registrar_estudiante(
    body: RegistrarEstudianteRequest,
    controller: RegistroController = Depends(get_registro_controller),
) -> RegistroResponse:
    """Registra un Estudiante vía invitación; endpoint público, sin JWT (aún no autenticado).

    Responde 409 si el email ya está registrado, 422 si la invitación no es válida
    (inexistente, vencida o ya usada — mismo status y mensaje para los tres casos, `US-1.1.3`)
    o si `password` no cumple INV-ID-11 (`US-ADJ-36`).
    """
    try:
        usuario, materia, _evento_invitacion, _evento_usuario = (
            await controller.registrar_estudiante(
                body.token, body.nombre, body.email, body.password
            )
        )
    except EmailYaRegistrado as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except (
        InvitacionInvalida,
        InvitacionVencida,
        InvitacionYaUsada,
        PasswordDemasiadoCorta,
        PasswordSinComplejidadSuficiente,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    # RegistrarEstudianteUseCase siempre crea un Usuario con perfil Estudiante — el isinstance
    # es la forma en que mypy puede probarlo, no una validación de negocio (Perfil también
    # admite Administrador/Docente, sin comision_id).
    assert isinstance(usuario.perfil, Estudiante)
    return RegistroResponse(
        id=usuario.id,
        nombre=usuario.nombre,
        email=usuario.email,
        comision_id=usuario.perfil.comision_id,
        materia=materia,
    )
