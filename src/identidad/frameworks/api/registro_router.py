"""Router FastAPI de registro de Estudiantes vía invitación."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from src.identidad.entities.errors import (
    InvitacionInvalida,
    InvitacionRevocada,
    InvitacionVencida,
    InvitacionYaUsada,
    PasswordDemasiadoCorta,
    PasswordSinComplejidadSuficiente,
)
from src.identidad.frameworks.api.errores_invitacion import error_http_de_invitacion
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
from src.identidad.interface_adapters.presenters.identidad_presenter import (
    InvitacionPreviewSalida,
    RegistroSalida,
)

router = APIRouter(prefix="/identidad", tags=["identidad"])


@router.get("/invitaciones/{token}", response_model=InvitacionPreviewResponse)
async def obtener_invitacion(
    token: str,
    controller: InvitacionesController = Depends(get_invitaciones_controller),
) -> InvitacionPreviewSalida:
    """Vista previa de una invitación por token, sin consumirla; endpoint público, sin JWT.

    Responde 404 si el token no corresponde a ninguna invitación, o 422 si ya venció, la
    desactivaron o ya fue usada; `detail.codigo` informa el motivo (`invitacion_invalida`,
    `invitacion_vencida`, `invitacion_revocada` o `invitacion_usada`, `US-ADJ-67`) porque es una
    consulta anónima por token, sin riesgo de enumerar invitaciones ajenas (`US-ADJ-08`).
    """
    try:
        return await controller.obtener_invitacion(token)
    except (InvitacionInvalida, InvitacionVencida, InvitacionRevocada, InvitacionYaUsada) as exc:
        raise error_http_de_invitacion(exc, status_invalida=status.HTTP_404_NOT_FOUND) from exc


@router.post("/registro", response_model=RegistroResponse, status_code=status.HTTP_201_CREATED)
async def registrar_estudiante(
    body: RegistrarEstudianteRequest,
    controller: RegistroController = Depends(get_registro_controller),
) -> RegistroSalida:
    """Registra un Estudiante vía invitación; endpoint público, sin JWT (aún no autenticado).

    Responde 409 si el email ya está registrado, 422 si la invitación no es válida (inexistente,
    vencida, desactivada o ya usada) o si `password` no cumple INV-ID-11 (`US-ADJ-36`). El
    `detail.codigo` distingue el motivo, y `password_invalida` no se confunde con un link inválido
    (`US-ADJ-67`).
    """
    try:
        return await controller.registrar_estudiante(
            body.token, body.nombre, body.email, body.password
        )
    except (
        InvitacionInvalida,
        InvitacionVencida,
        InvitacionRevocada,
        InvitacionYaUsada,
        PasswordDemasiadoCorta,
        PasswordSinComplejidadSuficiente,
    ) as exc:
        raise error_http_de_invitacion(
            exc, status_invalida=status.HTTP_422_UNPROCESSABLE_CONTENT
        ) from exc
