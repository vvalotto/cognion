"""Router FastAPI de operaciones sobre evaluaciones de un Estudiante."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.actividad_evaluativa.entities.errors import (
    ActividadNoExiste,
    EstudianteNoExiste,
    FueraDePeriodo,
)
from src.actividad_evaluativa.frameworks.api.schemas import (
    EvaluacionResponse,
    IniciarEvaluacionRequest,
    PreguntaAsignadaResponse,
)
from src.actividad_evaluativa.frameworks.dependencies import (
    get_current_user,
    get_evaluaciones_controller,
    require_estudiante,
)
from src.actividad_evaluativa.interface_adapters.controllers.evaluaciones_controller import (
    EvaluacionesController,
)
from src.shared.entities.jwt import JWTPayload

router = APIRouter(prefix="/evaluaciones", tags=["actividad_evaluativa"])


@router.post(
    "",
    response_model=EvaluacionResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_estudiante)],
)
async def iniciar_evaluacion(
    body: IniciarEvaluacionRequest,
    usuario: JWTPayload = Depends(get_current_user),
    controller: EvaluacionesController = Depends(get_evaluaciones_controller),
) -> EvaluacionResponse:
    """Inicia la evaluación del Estudiante autenticado, o retoma la existente (INV-AE-05/06).

    Responde 404/422 ante los rechazos de dominio.
    """
    try:
        evaluacion, _creada = await controller.iniciar_evaluacion(
            body.actividad_id, usuario.usuario_id
        )
    except (ActividadNoExiste, EstudianteNoExiste) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except FueraDePeriodo as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    return EvaluacionResponse(
        id=evaluacion.id,
        actividad_id=evaluacion.actividad_id,
        estudiante_id=evaluacion.estudiante_id,
        preguntas_asignadas=[
            PreguntaAsignadaResponse(pregunta_id=p.pregunta_id, orden=p.orden)
            for p in evaluacion.preguntas_asignadas
        ],
        estado=evaluacion.estado.value,
        iniciada_en=evaluacion.iniciada_en,
    )
