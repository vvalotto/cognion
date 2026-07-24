"""Router FastAPI de operaciones sobre comisiones."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.identidad.entities.errors import ComisionNoExiste, UsuarioNoEsDocente
from src.identidad.frameworks.api.schemas import (
    AsignarDocenteRequest,
    ComisionResponse,
    CrearComisionRequest,
)
from src.identidad.frameworks.dependencies import get_comisiones_controller, require_administrador
from src.identidad.interface_adapters.controllers.comisiones_controller import ComisionesController

router = APIRouter(prefix="/comisiones", tags=["identidad"])


@router.post(
    "",
    response_model=ComisionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_administrador)],
)
async def crear_comision(
    body: CrearComisionRequest,
    controller: ComisionesController = Depends(get_comisiones_controller),
) -> ComisionResponse:
    """Crea una comisión nueva a nombre del administrador indicado."""
    comision, _evento = await controller.crear_comision(
        body.materia, body.horario, body.administrador_id
    )
    return ComisionResponse(
        id=comision.id,
        materia=comision.materia,
        horario=comision.horario,
        administrador_id=comision.administrador_id,
        docentes_asignados=comision.docentes_asignados,
    )


@router.post(
    "/{comision_id}/docentes",
    response_model=ComisionResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_administrador)],
)
async def asignar_docente(
    comision_id: UUID,
    body: AsignarDocenteRequest,
    controller: ComisionesController = Depends(get_comisiones_controller),
) -> ComisionResponse:
    """Asigna un docente a la comisión; responde 422/404 según el error de dominio."""
    try:
        comision, _evento = await controller.asignar_docente(comision_id, body.docente_id)
    except UsuarioNoEsDocente as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    except ComisionNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return ComisionResponse(
        id=comision.id,
        materia=comision.materia,
        horario=comision.horario,
        administrador_id=comision.administrador_id,
        docentes_asignados=comision.docentes_asignados,
    )
