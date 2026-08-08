"""Router FastAPI de operaciones sobre preguntas."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.banco_preguntas.entities.errors import BancoNoExiste, OpcionesInvalidas
from src.banco_preguntas.entities.opcion import Opcion
from src.banco_preguntas.frameworks.api.schemas import (
    CargarPreguntaOpcionMultipleRequest,
    CargarPreguntaVerdaderoFalsoRequest,
    PreguntaOpcionMultipleResponse,
    PreguntaVerdaderoFalsoResponse,
)
from src.banco_preguntas.frameworks.dependencies import get_preguntas_controller, require_docente
from src.banco_preguntas.interface_adapters.controllers.preguntas_controller import (
    PreguntasController,
)

router = APIRouter(prefix="/preguntas", tags=["banco_preguntas"])


@router.post(
    "/opcion-multiple",
    response_model=PreguntaOpcionMultipleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_docente)],
)
async def cargar_pregunta_opcion_multiple(
    body: CargarPreguntaOpcionMultipleRequest,
    controller: PreguntasController = Depends(get_preguntas_controller),
) -> PreguntaOpcionMultipleResponse:
    """Carga una pregunta de opción múltiple.

    Responde 404 si el banco no existe, 422 si las opciones son inválidas.
    """
    try:
        pregunta, _evento = await controller.cargar_pregunta_opcion_multiple(
            banco_id=body.banco_id,
            texto=body.texto,
            opciones=[Opcion(texto=o.texto, es_correcta=o.es_correcta) for o in body.opciones],
            unidad_tematica=body.unidad_tematica,
            tema=body.tema,
            dificultad=body.dificultad,
            importancia=body.importancia,
        )
    except BancoNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except OpcionesInvalidas as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    return PreguntaOpcionMultipleResponse(
        id=pregunta.id,
        banco_id=pregunta.banco_id,
        texto=pregunta.texto,
        opciones=[{"texto": o.texto, "es_correcta": o.es_correcta} for o in pregunta.opciones],
        unidad_tematica=pregunta.unidad_tematica,
        tema=pregunta.tema,
        dificultad=pregunta.dificultad,
        importancia=pregunta.importancia,
        activa=pregunta.activa,
    )


@router.post(
    "/verdadero-falso",
    response_model=PreguntaVerdaderoFalsoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_docente)],
)
async def cargar_pregunta_verdadero_falso(
    body: CargarPreguntaVerdaderoFalsoRequest,
    controller: PreguntasController = Depends(get_preguntas_controller),
) -> PreguntaVerdaderoFalsoResponse:
    """Carga una pregunta Verdadero/Falso.

    Responde 404 si el banco no existe.
    """
    try:
        pregunta, _evento = await controller.cargar_pregunta_verdadero_falso(
            banco_id=body.banco_id,
            texto=body.texto,
            respuesta_correcta=body.respuesta_correcta,
            unidad_tematica=body.unidad_tematica,
            tema=body.tema,
            dificultad=body.dificultad,
            importancia=body.importancia,
        )
    except BancoNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return PreguntaVerdaderoFalsoResponse(
        id=pregunta.id,
        banco_id=pregunta.banco_id,
        texto=pregunta.texto,
        respuesta_correcta=pregunta.respuesta_correcta,
        unidad_tematica=pregunta.unidad_tematica,
        tema=pregunta.tema,
        dificultad=pregunta.dificultad,
        importancia=pregunta.importancia,
        activa=pregunta.activa,
    )
