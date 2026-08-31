"""Router FastAPI de operaciones sobre evaluaciones de un Estudiante."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

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
from src.actividad_evaluativa.entities.evaluacion import Evaluacion
from src.actividad_evaluativa.entities.ports.pregunta_consulta_port import PreguntaConsultaPort
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
    get_pregunta_consulta_port,
    require_estudiante,
)
from src.actividad_evaluativa.interface_adapters.controllers.evaluaciones_controller import (
    EvaluacionesController,
)
from src.shared.entities.jwt import JWTPayload

router = APIRouter(prefix="/evaluaciones", tags=["actividad_evaluativa"])


async def _a_response(
    evaluacion: Evaluacion, pregunta_consulta: PreguntaConsultaPort
) -> EvaluacionResponse:
    """Adapta una `Evaluacion` del dominio a `EvaluacionResponse` — reusado por los 4 endpoints.

    Enriquece cada `PreguntaAsignada` con `enunciado`/`opciones` vía `PreguntaConsultaPort`
    (`US-3.4.6`, sin la respuesta correcta) y deriva `preguntas_respondidas` de
    `evaluacion.respuestas` — ids únicos, sin importar cuántos intentos tuvo cada una.
    """
    preguntas_asignadas = []
    for p in evaluacion.preguntas_asignadas:
        contenido = await pregunta_consulta.obtener_contenido(p.pregunta_id)
        preguntas_asignadas.append(
            PreguntaAsignadaResponse(
                pregunta_id=p.pregunta_id,
                orden=p.orden,
                enunciado=contenido.texto,
                opciones=contenido.opciones,
            )
        )

    preguntas_respondidas = list(
        dict.fromkeys(respuesta.pregunta_id for respuesta in evaluacion.respuestas)
    )

    return EvaluacionResponse(
        id=evaluacion.id,
        actividad_id=evaluacion.actividad_id,
        estudiante_id=evaluacion.estudiante_id,
        preguntas_asignadas=preguntas_asignadas,
        preguntas_respondidas=preguntas_respondidas,
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
    pregunta_consulta: PreguntaConsultaPort = Depends(get_pregunta_consulta_port),
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

    return await _a_response(evaluacion, pregunta_consulta)


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
    pregunta_consulta: PreguntaConsultaPort = Depends(get_pregunta_consulta_port),
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

    return await _a_response(evaluacion, pregunta_consulta)


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
    pregunta_consulta: PreguntaConsultaPort = Depends(get_pregunta_consulta_port),
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

    return await _a_response(evaluacion, pregunta_consulta)


@router.post(
    "/{evaluacion_id}/finalizar",
    response_model=EvaluacionResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_estudiante)],
)
async def finalizar_evaluacion(
    evaluacion_id: UUID,
    usuario: JWTPayload = Depends(get_current_user),
    controller: EvaluacionesController = Depends(get_evaluaciones_controller),
    pregunta_consulta: PreguntaConsultaPort = Depends(get_pregunta_consulta_port),
) -> EvaluacionResponse:
    """Finaliza explícitamente la evaluación del Estudiante autenticado (RF-13).

    Responde 404/422 ante los rechazos de dominio. No valida período vigente.
    """
    try:
        evaluacion = await controller.finalizar_evaluacion(evaluacion_id, usuario.usuario_id)
    except EvaluacionNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EvaluacionYaFinalizada as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    return await _a_response(evaluacion, pregunta_consulta)
