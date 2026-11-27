"""Router FastAPI de operaciones sobre comisiones."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from src.identidad.entities.errors import (
    MateriaNoExiste,
)
from src.identidad.frameworks.api.schemas import (
    AsignarDocenteRequest,
    ComisionResponse,
    CrearComisionRequest,
    EditarComisionRequest,
    EstudianteResumenResponse,
)
from src.identidad.frameworks.dependencies import (
    get_comisiones_controller,
    get_comisiones_query_controller,
    get_current_user,
    require_administrador,
    require_docente_o_administrador,
)
from src.identidad.interface_adapters.controllers.comisiones_controller import ComisionesController
from src.identidad.interface_adapters.controllers.comisiones_query_controller import (
    ComisionesQueryController,
)
from src.identidad.interface_adapters.presenters.identidad_presenter import (
    ComisionSalida,
    EstudianteResumenSalida,
)
from src.shared.entities.jwt import JWTPayload
from src.shared.entities.tipo_perfil import TipoPerfil


def _docente_id_o_none(usuario: JWTPayload) -> UUID | None:
    """`usuario_id` si es Docente, `None` si es Administrador (sin filtro, ve todo)."""
    return usuario.usuario_id if usuario.rol is TipoPerfil.DOCENTE else None


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
) -> ComisionSalida:
    """Crea una comisión nueva a nombre del administrador indicado; 422 si la materia no existe."""
    try:
        return await controller.crear_comision(body.materia_id, body.horario, body.administrador_id)
    except MateriaNoExiste as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc


@router.get(
    "/{comision_id}",
    response_model=ComisionResponse,
    dependencies=[Depends(require_docente_o_administrador)],
)
async def obtener_comision(
    comision_id: UUID,
    usuario: JWTPayload = Depends(get_current_user),
    controller: ComisionesQueryController = Depends(get_comisiones_query_controller),
) -> ComisionSalida:
    """Detalle de una comisión puntual; 404 si `comision_id` no existe (`US-ADJ-25`).

    403 si el Docente que llama no está asignado a esta comisión (`US-ADJ-57`).
    """
    return await controller.obtener_comision(comision_id, _docente_id_o_none(usuario))


@router.get(
    "/{comision_id}/estudiantes",
    response_model=list[EstudianteResumenResponse],
    dependencies=[Depends(require_docente_o_administrador)],
)
async def listar_estudiantes(
    comision_id: UUID,
    usuario: JWTPayload = Depends(get_current_user),
    controller: ComisionesQueryController = Depends(get_comisiones_query_controller),
) -> list[EstudianteResumenSalida]:
    """Estudiantes inscriptos en la comisión; 404 si `comision_id` no existe (`US-4.2.2`).

    403 si el Docente que llama no está asignado a esta comisión (`US-ADJ-57`).
    """
    return await controller.listar_estudiantes(comision_id, _docente_id_o_none(usuario))


@router.patch(
    "/{comision_id}",
    response_model=ComisionResponse,
    dependencies=[Depends(require_administrador)],
)
async def editar_comision(
    comision_id: UUID,
    body: EditarComisionRequest,
    controller: ComisionesController = Depends(get_comisiones_controller),
) -> ComisionSalida:
    """Corrige el horario de una comisión existente; 404 si no existe."""
    return await controller.editar_comision(comision_id, body.horario)


@router.delete(
    "/{comision_id}",
    response_model=None,
    dependencies=[Depends(require_administrador)],
)
async def eliminar_comision(
    comision_id: UUID,
    controller: ComisionesController = Depends(get_comisiones_controller),
) -> ComisionSalida | Response:
    """Borra la comisión, o la deshabilita si tiene estudiantes inscriptos.

    204 si se borró físicamente; 200 con la comisión (`activa=false`) si se deshabilitó.
    404 si la comisión no existe.
    """
    comision = await controller.eliminar_comision(comision_id)

    if comision is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return comision


@router.post(
    "/{comision_id}/activar",
    response_model=ComisionResponse,
    dependencies=[Depends(require_administrador)],
)
async def activar_comision(
    comision_id: UUID,
    controller: ComisionesController = Depends(get_comisiones_controller),
) -> ComisionSalida:
    """Reactiva una comisión deshabilitada; 404 si no existe."""
    return await controller.activar_comision(comision_id)


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
) -> ComisionSalida:
    """Asigna un docente a la comisión; responde 422/404 según el error de dominio."""
    return await controller.asignar_docente(comision_id, body.docente_id)
