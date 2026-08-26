"""Router FastAPI de operaciones sobre actividades de período abierto."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.actividad_evaluativa.entities.errors import (
    CantidadIntentosInvalida,
    MateriaNoExiste,
    PeriodoInvalido,
    PreguntasInsuficientes,
)
from src.actividad_evaluativa.frameworks.api.schemas import (
    ActividadResponse,
    CrearActividadRequest,
)
from src.actividad_evaluativa.frameworks.dependencies import (
    get_actividades_controller,
    require_docente,
)
from src.actividad_evaluativa.interface_adapters.controllers.actividades_controller import (
    ActividadesController,
)

router = APIRouter(prefix="/actividades", tags=["actividad_evaluativa"])


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
        )
    except MateriaNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (PreguntasInsuficientes, PeriodoInvalido, CantidadIntentosInvalida) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    return ActividadResponse(
        id=actividad.id,
        materia_id=actividad.materia_id,
        fecha_apertura=actividad.fecha_apertura,
        fecha_cierre=actividad.fecha_cierre,
        cantidad_preguntas=actividad.cantidad_preguntas,
        cantidad_intentos_permitidos=actividad.cantidad_intentos_permitidos,
        cerrada_manualmente=actividad.cerrada_manualmente,
    )
