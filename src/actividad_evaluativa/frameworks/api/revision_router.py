"""Router FastAPI de la revisión completa de una evaluación finalizada (US-3.2.3, RF-13)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.actividad_evaluativa.entities.errors import EvaluacionNoExiste, EvaluacionNoFinalizada
from src.actividad_evaluativa.entities.revision_evaluacion import RevisionEvaluacion
from src.actividad_evaluativa.frameworks.api.schemas import (
    DetallePreguntaRevisionResponse,
    RevisionEvaluacionResponse,
)
from src.actividad_evaluativa.frameworks.dependencies import (
    get_current_user,
    get_revision_controller,
    require_estudiante,
)
from src.actividad_evaluativa.interface_adapters.controllers.revision_controller import (
    RevisionController,
)
from src.shared.entities.jwt import JWTPayload

router = APIRouter(prefix="/evaluaciones", tags=["actividad_evaluativa"])


def _a_response(revision: RevisionEvaluacion) -> RevisionEvaluacionResponse:
    """Adapta una `RevisionEvaluacion` del dominio a `RevisionEvaluacionResponse`."""
    return RevisionEvaluacionResponse(
        evaluacion_id=revision.evaluacion_id,
        cantidad_preguntas=revision.cantidad_preguntas,
        cantidad_correctas=revision.cantidad_correctas,
        cantidad_incorrectas=revision.cantidad_incorrectas,
        detalle=[
            DetallePreguntaRevisionResponse(
                pregunta_id=fila.pregunta_id,
                orden=fila.orden,
                texto=fila.texto,
                respondida=fila.respondida,
                contenido_propio=fila.contenido_propio,
                es_correcta=fila.es_correcta,
                contenido_correcto=fila.contenido_correcto,
                opciones=fila.opciones,
            )
            for fila in revision.detalle
        ],
    )


@router.get(
    "/{evaluacion_id}/revision",
    response_model=RevisionEvaluacionResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_estudiante)],
)
async def obtener_revision(
    evaluacion_id: UUID,
    usuario: JWTPayload = Depends(get_current_user),
    controller: RevisionController = Depends(get_revision_controller),
) -> RevisionEvaluacionResponse:
    """Devuelve la revisión completa de la evaluación del Estudiante autenticado (RF-13).

    Responde 404/422 ante los rechazos de dominio — 422 si todavía no fue finalizada.
    """
    try:
        revision = await controller.obtener_revision(evaluacion_id, usuario.usuario_id)
    except EvaluacionNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EvaluacionNoFinalizada as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    return _a_response(revision)
