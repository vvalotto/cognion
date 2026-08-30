"""Router FastAPI de operaciones sobre actividades de período abierto."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.actividad_evaluativa.entities.actividad_evaluativa_periodo_abierto import (
    ActividadEvaluativaPeriodoAbierto,
)
from src.actividad_evaluativa.entities.errors import (
    ActividadNoExiste,
    ActividadYaCerrada,
    CantidadIntentosInvalida,
    MateriaNoExiste,
    NoSePuedeAcortarConEvaluacionesActivas,
    PeriodoInvalido,
    PreguntasInsuficientes,
)
from src.actividad_evaluativa.entities.ports.actividad_query_port import ActividadResumen
from src.actividad_evaluativa.frameworks.api.schemas import (
    ActividadResponse,
    ActividadResumenResponse,
    CrearActividadRequest,
    ModificarPeriodoDisponibilidadRequest,
    ModificarTituloRequest,
)
from src.actividad_evaluativa.frameworks.dependencies import (
    get_actividades_controller,
    get_actividades_query_controller,
    require_docente,
)
from src.actividad_evaluativa.interface_adapters.controllers.actividades_controller import (
    ActividadesController,
)
from src.actividad_evaluativa.interface_adapters.controllers.actividades_query_controller import (
    ActividadesQueryController,
)

router = APIRouter(prefix="/actividades", tags=["actividad_evaluativa"])


def _a_response(actividad: ActividadEvaluativaPeriodoAbierto) -> ActividadResponse:
    """Arma el `ActividadResponse` — extraído para no repetirlo en cada endpoint."""
    return ActividadResponse(
        id=actividad.id,
        materia_id=actividad.materia_id,
        fecha_apertura=actividad.fecha_apertura,
        fecha_cierre=actividad.fecha_cierre,
        cantidad_preguntas=actividad.cantidad_preguntas,
        cantidad_intentos_permitidos=actividad.cantidad_intentos_permitidos,
        cerrada_manualmente=actividad.cerrada_manualmente,
        titulo=actividad.titulo,
    )


def _estado_actividad(resumen: ActividadResumen, ahora: datetime) -> str:
    """Deriva el estado de una actividad — no persiste un campo propio (`US-3.4.2`).

    `cerrada` si se cerró manualmente o si `fecha_cierre` ya pasó; `programada` si todavía no
    abrió; `en_curso` en cualquier otro caso.
    """
    if resumen.cerrada_manualmente or resumen.fecha_cierre <= ahora:
        return "cerrada"
    if resumen.fecha_apertura > ahora:
        return "programada"
    return "en_curso"


def _a_resumen_response(resumen: ActividadResumen, ahora: datetime) -> ActividadResumenResponse:
    """Arma el `ActividadResumenResponse` con el estado ya derivado."""
    return ActividadResumenResponse(
        id=resumen.id,
        materia_id=resumen.materia_id,
        titulo=resumen.titulo,
        fecha_apertura=resumen.fecha_apertura,
        fecha_cierre=resumen.fecha_cierre,
        cantidad_preguntas=resumen.cantidad_preguntas,
        cantidad_intentos_permitidos=resumen.cantidad_intentos_permitidos,
        estado=_estado_actividad(resumen, ahora),
        cerrada_manualmente=resumen.cerrada_manualmente,
        cantidad_evaluaciones_activas=resumen.cantidad_evaluaciones_activas,
        cantidad_evaluaciones_finalizadas=resumen.cantidad_evaluaciones_finalizadas,
    )


@router.get(
    "",
    response_model=list[ActividadResumenResponse],
    dependencies=[Depends(require_docente)],
)
async def listar_actividades(
    materia_id: UUID = Query(...),
    controller: ActividadesQueryController = Depends(get_actividades_query_controller),
) -> list[ActividadResumenResponse]:
    """Lista las actividades de una materia con estado derivado y conteos (`US-3.4.2`, RF-11)."""
    resumenes = await controller.listar_actividades(materia_id)
    ahora = datetime.now(UTC)
    return [_a_resumen_response(resumen, ahora) for resumen in resumenes]


@router.get(
    "/{actividad_id}",
    response_model=ActividadResumenResponse,
    dependencies=[Depends(require_docente)],
)
async def obtener_actividad(
    actividad_id: UUID,
    controller: ActividadesQueryController = Depends(get_actividades_query_controller),
) -> ActividadResumenResponse:
    """Detalle de una actividad puntual, con estado derivado y conteos (`US-3.4.4`, RF-11b)."""
    try:
        resumen = await controller.obtener_actividad(actividad_id)
    except ActividadNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    ahora = datetime.now(UTC)
    return _a_resumen_response(resumen, ahora)


@router.post(
    "",
    response_model=ActividadResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_docente)],
)
async def crear_actividad(
    body: CrearActividadRequest,
    controller: ActividadesController = Depends(get_actividades_controller),
) -> ActividadResponse:
    """Crea una actividad de período abierto; responde 404/422 ante los rechazos de dominio."""
    try:
        actividad, _evento = await controller.crear_actividad(
            body.materia_id,
            body.fecha_apertura,
            body.fecha_cierre,
            body.cantidad_preguntas,
            body.cantidad_intentos_permitidos,
            body.titulo,
        )
    except MateriaNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (PreguntasInsuficientes, PeriodoInvalido, CantidadIntentosInvalida) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    return _a_response(actividad)


@router.patch(
    "/{actividad_id}/periodo",
    response_model=ActividadResponse,
    dependencies=[Depends(require_docente)],
)
async def modificar_periodo_disponibilidad(
    actividad_id: UUID,
    body: ModificarPeriodoDisponibilidadRequest,
    controller: ActividadesController = Depends(get_actividades_controller),
) -> ActividadResponse:
    """Extiende o acorta `fecha_cierre` de una actividad vigente (RF-11b)."""
    try:
        actividad = await controller.modificar_periodo_disponibilidad(
            actividad_id, body.nueva_fecha_cierre
        )
    except ActividadNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (
        PeriodoInvalido,
        NoSePuedeAcortarConEvaluacionesActivas,
        ActividadYaCerrada,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    return _a_response(actividad)


@router.patch(
    "/{actividad_id}/titulo",
    response_model=ActividadResponse,
    dependencies=[Depends(require_docente)],
)
async def modificar_titulo(
    actividad_id: UUID,
    body: ModificarTituloRequest,
    controller: ActividadesController = Depends(get_actividades_controller),
) -> ActividadResponse:
    """Edita el título de una actividad, sin importar su estado (`US-3.4.9`)."""
    try:
        actividad = await controller.modificar_titulo(actividad_id, body.nuevo_titulo)
    except ActividadNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _a_response(actividad)


@router.post(
    "/{actividad_id}/cerrar",
    response_model=ActividadResponse,
    dependencies=[Depends(require_docente)],
)
async def cerrar_actividad(
    actividad_id: UUID,
    controller: ActividadesController = Depends(get_actividades_controller),
) -> ActividadResponse:
    """Cierra manualmente la actividad, finalizando en cascada sus evaluaciones activas (RF-11b)."""
    try:
        actividad = await controller.cerrar_actividad(actividad_id)
    except ActividadNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ActividadYaCerrada as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    return _a_response(actividad)
