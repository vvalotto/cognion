"""Router FastAPI del link de invitación grupal de una comisión (`US-ADJ-67`)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from src.identidad.frameworks.api.schemas import (
    GenerarInvitacionGrupalRequest,
    InvitacionGrupalEstadoResponse,
    InvitacionGrupalResponse,
)
from src.identidad.frameworks.dependencies import (
    get_current_user,
    get_invitaciones_grupales_controller,
    require_docente,
)
from src.identidad.interface_adapters.controllers.invitaciones_grupales_controller import (
    InvitacionesGrupalesController,
)
from src.identidad.interface_adapters.presenters.identidad_presenter import (
    InvitacionGrupalEstadoSalida,
    InvitacionGrupalSalida,
)
from src.shared.entities.jwt import JWTPayload

router = APIRouter(
    prefix="/comisiones", tags=["identidad"], dependencies=[Depends(require_docente)]
)


@router.post(
    "/{comision_id}/invitaciones-grupales",
    response_model=InvitacionGrupalResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generar_invitacion_grupal(
    comision_id: UUID,
    body: GenerarInvitacionGrupalRequest,
    usuario: JWTPayload = Depends(get_current_user),
    controller: InvitacionesGrupalesController = Depends(get_invitaciones_grupales_controller),
) -> InvitacionGrupalSalida:
    """Genera el link grupal de la comisión y desactiva el grupal vigente anterior.

    Responde 403 si el Docente no está asignado, 404 si la comisión no existe y 422 si
    `duracion_minutos` no es 15, 60 ni 1440.
    """
    return await controller.generar(comision_id, usuario.usuario_id, body.duracion_minutos)


@router.get(
    "/{comision_id}/invitaciones-grupales/ultima",
    response_model=InvitacionGrupalEstadoResponse | None,
)
async def obtener_ultima_invitacion_grupal(
    comision_id: UUID,
    usuario: JWTPayload = Depends(get_current_user),
    controller: InvitacionesGrupalesController = Depends(get_invitaciones_grupales_controller),
) -> InvitacionGrupalEstadoSalida | None:
    """Devuelve el estado del último link grupal, o `null` si la comisión nunca generó uno."""
    return await controller.obtener_ultima(comision_id, usuario.usuario_id)


@router.post(
    "/{comision_id}/invitaciones-grupales/{invitacion_id}/revocar",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revocar_invitacion_grupal(
    comision_id: UUID,
    invitacion_id: UUID,
    usuario: JWTPayload = Depends(get_current_user),
    controller: InvitacionesGrupalesController = Depends(get_invitaciones_grupales_controller),
) -> Response:
    """Desactiva el link grupal; idempotente. 403 si el Docente no está asignado, 404 si no hay."""
    await controller.revocar(comision_id, invitacion_id, usuario.usuario_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
