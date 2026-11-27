"""Router FastAPI de operaciones sobre evaluaciones de un Estudiante."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.actividad_evaluativa.frameworks.api.schemas import (
    EvaluacionResponse,
    IniciarEvaluacionRequest,
    RegistrarRespuestaRequest,
    RespuestaResponse,
)
from src.actividad_evaluativa.frameworks.dependencies import (
    get_current_user,
    get_evaluaciones_controller,
    get_evaluaciones_estado_controller,
    require_estudiante,
)
from src.actividad_evaluativa.interface_adapters.controllers.evaluaciones_controller import (
    EvaluacionesController,
)
from src.actividad_evaluativa.interface_adapters.controllers.evaluaciones_estado_controller import (
    EvaluacionesEstadoController,
)
from src.actividad_evaluativa.interface_adapters.presenters.evaluacion_presenter import (
    EvaluacionSalida,
    RespuestaSalida,
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
) -> EvaluacionSalida:
    """Inicia la evaluación del Estudiante autenticado, o retoma la existente (INV-AE-05/06).

    Responde 404/422 ante los rechazos de dominio.
    """
    return await controller.iniciar_evaluacion(body.actividad_id, usuario.usuario_id)


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
) -> RespuestaSalida:
    """Confirma una respuesta del Estudiante autenticado — persistencia atómica (INV-AE-09).

    Responde 404/422 ante los rechazos de dominio. No informa `es_correcta` en la respuesta.
    """
    return await controller.registrar_respuesta(
        evaluacion_id, usuario.usuario_id, body.pregunta_id, body.contenido
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
    controller: EvaluacionesEstadoController = Depends(get_evaluaciones_estado_controller),
) -> EvaluacionSalida:
    """Pausa explícitamente la evaluación del Estudiante autenticado (INV-AE-12).

    Responde 404/422 ante los rechazos de dominio. No valida período vigente.
    """
    return await controller.suspender_evaluacion(evaluacion_id, usuario.usuario_id)


@router.post(
    "/{evaluacion_id}/reanudar",
    response_model=EvaluacionResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_estudiante)],
)
async def reanudar_evaluacion(
    evaluacion_id: UUID,
    usuario: JWTPayload = Depends(get_current_user),
    controller: EvaluacionesEstadoController = Depends(get_evaluaciones_estado_controller),
) -> EvaluacionSalida:
    """Reanuda explícitamente la evaluación suspendida del Estudiante autenticado (INV-AE-11).

    Responde 404/422 ante los rechazos de dominio.
    """
    return await controller.reanudar_evaluacion(evaluacion_id, usuario.usuario_id)


@router.post(
    "/{evaluacion_id}/finalizar",
    response_model=EvaluacionResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_estudiante)],
)
async def finalizar_evaluacion(
    evaluacion_id: UUID,
    usuario: JWTPayload = Depends(get_current_user),
    controller: EvaluacionesEstadoController = Depends(get_evaluaciones_estado_controller),
) -> EvaluacionSalida:
    """Finaliza explícitamente la evaluación del Estudiante autenticado (RF-13).

    Responde 404/422 ante los rechazos de dominio. No valida período vigente.
    """
    return await controller.finalizar_evaluacion(evaluacion_id, usuario.usuario_id)
