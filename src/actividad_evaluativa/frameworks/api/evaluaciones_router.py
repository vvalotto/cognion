"""Router FastAPI de operaciones sobre evaluaciones de un Estudiante."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.actividad_evaluativa.entities.evaluacion import Evaluacion
from src.actividad_evaluativa.entities.errors import (
    ActividadNoExiste,
    EstudianteNoExiste,
    EvaluacionNoExiste,
    EvaluacionNoSuspendida,
    EvaluacionSuspendida,
    EvaluacionYaFinalizada,
    EvaluacionYaSuspendida,
    FueraDePeriodo,
    IntentosAgotados,
    PreguntaNoAsignada,
)
from src.actividad_evaluativa.frameworks.api.schemas import (
    EvaluacionResponse,
    IniciarEvaluacionRequest,
    PreguntaAsignadaResponse,
    RegistrarRespuestaRequest,
    RespuestaResponse,
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


def _a_response(evaluacion: Evaluacion) -> EvaluacionResponse:
    """Adapta una `Evaluacion` del dominio a `EvaluacionResponse` — reusado por los 3 endpoints."""
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

    return _a_response(evaluacion)


@router.post(
    "/{evaluacion_id}/respuestas",
    response_model=RespuestaResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_estudiante)],
)
async def registrar_respuesta(
    evaluacion_id: UUID,
    body: RegistrarRespuestaRequest,
    usuario: JWTPayload = Depends(get_current_user),
    controller: EvaluacionesController = Depends(get_evaluaciones_controller),
) -> RespuestaResponse:
    """Confirma una respuesta del Estudiante autenticado — persistencia atómica (INV-AE-09).

    Responde 404/422 ante los rechazos de dominio. No informa `es_correcta` en la respuesta.
    """
    try:
        respuesta = await controller.registrar_respuesta(
            evaluacion_id, usuario.usuario_id, body.pregunta_id, body.contenido
        )
    except (EvaluacionNoExiste, PreguntaNoAsignada) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (
        IntentosAgotados,
        EvaluacionSuspendida,
        EvaluacionYaFinalizada,
        FueraDePeriodo,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    return RespuestaResponse(
        id=respuesta.id,
        pregunta_id=respuesta.pregunta_id,
        numero_intento=respuesta.numero_intento,
        confirmada_en=respuesta.confirmada_en,
    )


@router.post(
    "/{evaluacion_id}/suspender",
    response_model=EvaluacionResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_estudiante)],
)
async def suspender_evaluacion(
    evaluacion_id: UUID,
    usuario: JWTPayload = Depends(get_current_user),
    controller: EvaluacionesController = Depends(get_evaluaciones_controller),
) -> EvaluacionResponse:
    """Pausa explícitamente la evaluación del Estudiante autenticado (INV-AE-12).

    Responde 404/422 ante los rechazos de dominio. No valida período vigente.
    """
    try:
        evaluacion = await controller.suspender_evaluacion(evaluacion_id, usuario.usuario_id)
    except EvaluacionNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (EvaluacionYaSuspendida, EvaluacionYaFinalizada) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    return _a_response(evaluacion)


@router.post(
    "/{evaluacion_id}/reanudar",
    response_model=EvaluacionResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_estudiante)],
)
async def reanudar_evaluacion(
    evaluacion_id: UUID,
    usuario: JWTPayload = Depends(get_current_user),
    controller: EvaluacionesController = Depends(get_evaluaciones_controller),
) -> EvaluacionResponse:
    """Reanuda explícitamente la evaluación suspendida del Estudiante autenticado (INV-AE-11).

    Responde 404/422 ante los rechazos de dominio.
    """
    try:
        evaluacion = await controller.reanudar_evaluacion(evaluacion_id, usuario.usuario_id)
    except EvaluacionNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (EvaluacionNoSuspendida, EvaluacionYaFinalizada, FueraDePeriodo) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    return _a_response(evaluacion)
