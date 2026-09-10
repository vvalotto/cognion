"""Router FastAPI de operaciones sobre comisiones."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from src.identidad.entities.errors import ComisionNoExiste, MateriaNoExiste, UsuarioNoEsDocente
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
    require_administrador,
    require_docente_o_administrador,
)
from src.identidad.interface_adapters.controllers.comisiones_controller import ComisionesController
from src.identidad.interface_adapters.controllers.comisiones_query_controller import (
    ComisionesQueryController,
)

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
    """Crea una comisión nueva a nombre del administrador indicado; 422 si la materia no existe."""
    try:
        comision, _evento = await controller.crear_comision(
            body.materia_id, body.horario, body.administrador_id
        )
    except MateriaNoExiste as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    return ComisionResponse(
        id=comision.id,
        materia_id=comision.materia_id,
        horario=comision.horario,
        administrador_id=comision.administrador_id,
        docentes_asignados=comision.docentes_asignados,
        activa=comision.activa,
    )


@router.get(
    "/{comision_id}",
    response_model=ComisionResponse,
    dependencies=[Depends(require_docente_o_administrador)],
)
async def obtener_comision(
    comision_id: UUID,
    controller: ComisionesQueryController = Depends(get_comisiones_query_controller),
) -> ComisionResponse:
    """Detalle de una comisión puntual; 404 si `comision_id` no existe (`US-ADJ-25`)."""
    try:
        comision = await controller.obtener_comision(comision_id)
    except ComisionNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return ComisionResponse(
        id=comision.id,
        materia_id=comision.materia_id,
        horario=comision.horario,
        administrador_id=comision.administrador_id,
        docentes_asignados=comision.docentes_asignados,
        activa=comision.activa,
    )


@router.get(
    "/{comision_id}/estudiantes",
    response_model=list[EstudianteResumenResponse],
    dependencies=[Depends(require_docente_o_administrador)],
)
async def listar_estudiantes(
    comision_id: UUID,
    controller: ComisionesQueryController = Depends(get_comisiones_query_controller),
) -> list[EstudianteResumenResponse]:
    """Estudiantes inscriptos en la comisión; 404 si `comision_id` no existe (`US-4.2.2`)."""
    try:
        estudiantes = await controller.listar_estudiantes(comision_id)
    except ComisionNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [EstudianteResumenResponse(id=e.id, nombre=e.nombre) for e in estudiantes]


@router.patch(
    "/{comision_id}",
    response_model=ComisionResponse,
    dependencies=[Depends(require_administrador)],
)
async def editar_comision(
    comision_id: UUID,
    body: EditarComisionRequest,
    controller: ComisionesController = Depends(get_comisiones_controller),
) -> ComisionResponse:
    """Corrige el horario de una comisión existente; 404 si no existe."""
    try:
        comision = await controller.editar_comision(comision_id, body.horario)
    except ComisionNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return ComisionResponse(
        id=comision.id,
        materia_id=comision.materia_id,
        horario=comision.horario,
        administrador_id=comision.administrador_id,
        docentes_asignados=comision.docentes_asignados,
        activa=comision.activa,
    )


@router.delete(
    "/{comision_id}",
    response_model=None,
    dependencies=[Depends(require_administrador)],
)
async def eliminar_comision(
    comision_id: UUID,
    controller: ComisionesController = Depends(get_comisiones_controller),
) -> ComisionResponse | Response:
    """Borra la comisión, o la deshabilita si tiene estudiantes inscriptos.

    204 si se borró físicamente; 200 con la comisión (`activa=false`) si se deshabilitó.
    404 si la comisión no existe.
    """
    try:
        comision = await controller.eliminar_comision(comision_id)
    except ComisionNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    if comision is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return ComisionResponse(
        id=comision.id,
        materia_id=comision.materia_id,
        horario=comision.horario,
        administrador_id=comision.administrador_id,
        docentes_asignados=comision.docentes_asignados,
        activa=comision.activa,
    )


@router.post(
    "/{comision_id}/activar",
    response_model=ComisionResponse,
    dependencies=[Depends(require_administrador)],
)
async def activar_comision(
    comision_id: UUID,
    controller: ComisionesController = Depends(get_comisiones_controller),
) -> ComisionResponse:
    """Reactiva una comisión deshabilitada; 404 si no existe."""
    try:
        comision = await controller.activar_comision(comision_id)
    except ComisionNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return ComisionResponse(
        id=comision.id,
        materia_id=comision.materia_id,
        horario=comision.horario,
        administrador_id=comision.administrador_id,
        docentes_asignados=comision.docentes_asignados,
        activa=comision.activa,
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
        materia_id=comision.materia_id,
        horario=comision.horario,
        administrador_id=comision.administrador_id,
        docentes_asignados=comision.docentes_asignados,
        activa=comision.activa,
    )
