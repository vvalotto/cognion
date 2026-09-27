"""Router FastAPI de operaciones sobre invitaciones."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.identidad.entities.errors import (
    ComisionNoAutorizada,
    ComisionNoExiste,
    DocenteNoAsignadoAComision,
)
from src.identidad.frameworks.api.schemas import GenerarInvitacionRequest, InvitacionResponse
from src.identidad.frameworks.dependencies import (
    get_current_user,
    get_invitaciones_controller,
    require_docente,
)
from src.identidad.interface_adapters.controllers.invitaciones_controller import (
    InvitacionesController,
)
from src.shared.entities.jwt import JWTPayload

router = APIRouter(prefix="/comisiones", tags=["identidad"])


@router.post(
    "/{comision_id}/invitaciones",
    response_model=InvitacionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_docente)],
)
async def generar_invitacion(
    comision_id: UUID,
    body: GenerarInvitacionRequest,
    usuario: JWTPayload = Depends(get_current_user),
    controller: InvitacionesController = Depends(get_invitaciones_controller),
) -> InvitacionResponse:
    """Genera una invitación para la comisión; responde 422/404/403 según el error de dominio.

    403 si el Docente que llama no está asignado a `comision_id` (`US-ADJ-57`).
    """
    try:
        invitacion, _evento = await controller.generar_invitacion(
            comision_id, body.docente_id, body.email_destinatario, usuario.usuario_id
        )
    except ComisionNoAutorizada as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except DocenteNoAsignadoAComision as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    except ComisionNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return InvitacionResponse(
        id=invitacion.id,
        comision_id=invitacion.comision_id,
        docente_id=invitacion.docente_id,
        expira_en=invitacion.expira_en,
        token=invitacion.token,
    )
