"""Router FastAPI de operaciones sobre actividades de período abierto."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.actividad_evaluativa.frameworks.api.schemas import (
    ActividadResponse,
    ActividadResumenResponse,
    ActividadVisibleResponse,
    CrearActividadRequest,
    ModificarPeriodoDisponibilidadRequest,
    ModificarTituloRequest,
)
from src.actividad_evaluativa.frameworks.dependencies import (
    get_actividades_controller,
    get_actividades_estudiante_controller,
    get_actividades_query_controller,
    get_current_user,
    require_docente,
    require_estudiante,
)
from src.actividad_evaluativa.interface_adapters.controllers.actividades_controller import (
    ActividadesController,
)
from src.actividad_evaluativa.interface_adapters.controllers.actividades_estudiante_controller import (
    ActividadesEstudianteController,
)
from src.actividad_evaluativa.interface_adapters.controllers.actividades_query_controller import (
    ActividadesQueryController,
)
from src.actividad_evaluativa.interface_adapters.presenters.actividad_presenter import (
    ActividadResumenSalida,
    ActividadSalida,
    ActividadVisibleSalida,
)
from src.shared.entities.jwt import JWTPayload

router = APIRouter(prefix="/actividades", tags=["actividad_evaluativa"])


@router.get(
    "",
    response_model=list[ActividadResumenResponse],
    dependencies=[Depends(require_docente)],
)
async def listar_actividades(
    materia_id: UUID = Query(...),
    usuario: JWTPayload = Depends(get_current_user),
    controller: ActividadesQueryController = Depends(get_actividades_query_controller),
) -> list[ActividadResumenSalida]:
    """Lista las actividades de una materia con estado derivado y conteos (`US-3.4.2`, RF-11).

    El Docente solo ve las actividades de una materia donde tiene al menos una Comisión
    asignada (`US-ADJ-57`); 403 si no.
    """
    return await controller.listar_actividades(materia_id, usuario.usuario_id)


@router.get(
    "/mis-actividades",
    response_model=list[ActividadVisibleResponse],
    dependencies=[Depends(require_estudiante)],
)
async def listar_mis_actividades(
    materia_id: UUID = Query(...),
    usuario: JWTPayload = Depends(get_current_user),
    controller: ActividadesEstudianteController = Depends(get_actividades_estudiante_controller),
) -> list[ActividadVisibleSalida]:
    """Actividades de una materia con el `Badge` de estado del Estudiante autenticado (`US-3.4.5`).

    Registrada antes de `/{actividad_id}` — es una ruta literal, no debe resolverse como un
    `actividad_id`.
    """
    return await controller.listar_actividades_visibles(materia_id, usuario.usuario_id)


@router.get(
    "/{actividad_id}",
    response_model=ActividadResumenResponse,
    dependencies=[Depends(require_docente)],
)
async def obtener_actividad(
    actividad_id: UUID,
    usuario: JWTPayload = Depends(get_current_user),
    controller: ActividadesQueryController = Depends(get_actividades_query_controller),
) -> ActividadResumenSalida:
    """Detalle de una actividad puntual, con estado derivado y conteos (`US-3.4.4`, RF-11b).

    403 si el Docente no tiene ninguna Comisión asignada en la materia de la actividad
    (`US-ADJ-57`).
    """
    return await controller.obtener_actividad(actividad_id, usuario.usuario_id)


@router.post(
    "",
    response_model=ActividadResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_docente)],
)
async def crear_actividad(
    body: CrearActividadRequest,
    usuario: JWTPayload = Depends(get_current_user),
    controller: ActividadesController = Depends(get_actividades_controller),
) -> ActividadSalida:
    """Crea una actividad de período abierto; responde 404/422/403 ante los rechazos de dominio.

    403 si el Docente no tiene ninguna Comisión asignada en `materia_id`, o si alguna de
    `comisiones_ids` no es una Comisión propia (`US-ADJ-57`).
    """
    return await controller.crear_actividad(
        body.materia_id,
        body.fecha_apertura,
        body.fecha_cierre,
        body.cantidad_preguntas,
        body.cantidad_intentos_permitidos,
        body.titulo,
        frozenset(body.comisiones_ids),
        body.unidad_tematica,
        body.tema,
        usuario.usuario_id,
    )


@router.patch(
    "/{actividad_id}/periodo",
    response_model=ActividadResponse,
    dependencies=[Depends(require_docente)],
)
async def modificar_periodo_disponibilidad(
    actividad_id: UUID,
    body: ModificarPeriodoDisponibilidadRequest,
    usuario: JWTPayload = Depends(get_current_user),
    controller: ActividadesController = Depends(get_actividades_controller),
) -> ActividadSalida:
    """Extiende o acorta `fecha_cierre` de una actividad vigente (RF-11b).

    403 si el Docente no tiene ninguna Comisión asignada en la materia de la actividad
    (`US-ADJ-57`).
    """
    return await controller.modificar_periodo_disponibilidad(
        actividad_id, body.nueva_fecha_cierre, usuario.usuario_id
    )


@router.patch(
    "/{actividad_id}/titulo",
    response_model=ActividadResponse,
    dependencies=[Depends(require_docente)],
)
async def modificar_titulo(
    actividad_id: UUID,
    body: ModificarTituloRequest,
    usuario: JWTPayload = Depends(get_current_user),
    controller: ActividadesController = Depends(get_actividades_controller),
) -> ActividadSalida:
    """Edita el título de una actividad, sin importar su estado (`US-ADJ-10`).

    403 si el Docente no tiene ninguna Comisión asignada en la materia de la actividad
    (`US-ADJ-57`).
    """
    return await controller.modificar_titulo(actividad_id, body.nuevo_titulo, usuario.usuario_id)


@router.post(
    "/{actividad_id}/cerrar",
    response_model=ActividadResponse,
    dependencies=[Depends(require_docente)],
)
async def cerrar_actividad(
    actividad_id: UUID,
    usuario: JWTPayload = Depends(get_current_user),
    controller: ActividadesController = Depends(get_actividades_controller),
) -> ActividadSalida:
    """Cierra manualmente la actividad, finalizando en cascada sus evaluaciones activas (RF-11b).

    403 si el Docente no tiene ninguna Comisión asignada en la materia de la actividad
    (`US-ADJ-57`).
    """
    return await controller.cerrar_actividad(actividad_id, usuario.usuario_id)
