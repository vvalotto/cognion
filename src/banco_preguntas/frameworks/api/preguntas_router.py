"""Router FastAPI de operaciones sobre preguntas."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.banco_preguntas.frameworks.api.schemas import (
    CargarPreguntaOpcionMultipleRequest,
    CargarPreguntaVerdaderoFalsoRequest,
    EditarPreguntaRequest,
    PreguntaOpcionMultipleResponse,
    PreguntaVerdaderoFalsoResponse,
)
from src.banco_preguntas.frameworks.dependencies import (
    get_current_user,
    get_preguntas_controller,
    require_docente,
)
from src.banco_preguntas.interface_adapters.controllers.preguntas_controller import (
    PreguntasController,
)
from src.banco_preguntas.interface_adapters.presenters.banco_presenter import (
    PreguntaOpcionMultipleSalida,
    PreguntaSalida,
    PreguntaVerdaderoFalsoSalida,
)
from src.shared.entities.jwt import JWTPayload

router = APIRouter(prefix="/preguntas", tags=["banco_preguntas"])


@router.post(
    "/opcion-multiple",
    response_model=PreguntaOpcionMultipleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_docente)],
)
async def cargar_pregunta_opcion_multiple(
    body: CargarPreguntaOpcionMultipleRequest,
    usuario: JWTPayload = Depends(get_current_user),
    controller: PreguntasController = Depends(get_preguntas_controller),
) -> PreguntaOpcionMultipleSalida:
    """Carga una pregunta de opción múltiple.

    Responde 404 si el banco no existe, 422 si las opciones son inválidas, 403 si el Docente
    no tiene ninguna Comisión asignada en la materia del banco (`US-ADJ-57`).
    """
    return await controller.cargar_pregunta_opcion_multiple(
        banco_id=body.banco_id,
        texto=body.texto,
        unidad_tematica=body.unidad_tematica,
        tema=body.tema,
        dificultad=body.dificultad,
        importancia=body.importancia,
        opciones=[(o.texto, o.es_correcta) for o in body.opciones],
        docente_id=usuario.usuario_id,
    )


@router.post(
    "/verdadero-falso",
    response_model=PreguntaVerdaderoFalsoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_docente)],
)
async def cargar_pregunta_verdadero_falso(
    body: CargarPreguntaVerdaderoFalsoRequest,
    usuario: JWTPayload = Depends(get_current_user),
    controller: PreguntasController = Depends(get_preguntas_controller),
) -> PreguntaVerdaderoFalsoSalida:
    """Carga una pregunta Verdadero/Falso.

    Responde 404 si el banco no existe, 403 si el Docente no tiene ninguna Comisión
    asignada en la materia del banco (`US-ADJ-57`).
    """
    return await controller.cargar_pregunta_verdadero_falso(
        banco_id=body.banco_id,
        texto=body.texto,
        unidad_tematica=body.unidad_tematica,
        tema=body.tema,
        dificultad=body.dificultad,
        importancia=body.importancia,
        respuesta_correcta=body.respuesta_correcta,
        docente_id=usuario.usuario_id,
    )


@router.put(
    "/{pregunta_id}",
    response_model=PreguntaOpcionMultipleResponse | PreguntaVerdaderoFalsoResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_docente)],
)
async def editar_pregunta(
    pregunta_id: UUID,
    body: EditarPreguntaRequest,
    usuario: JWTPayload = Depends(get_current_user),
    controller: PreguntasController = Depends(get_preguntas_controller),
) -> PreguntaSalida:
    """Edita una pregunta existente (texto, opciones/respuesta, metadatos).

    El tipo de la pregunta (Opción Múltiple / Verdadero-Falso) no es editable.
    Responde 404 si la pregunta no existe, 409 si está inactiva, 422 si las opciones editadas
    son inválidas, 403 si el Docente no tiene ninguna Comisión asignada en la materia del
    banco de la pregunta (`US-ADJ-57`).
    """
    return await controller.editar_pregunta(
        pregunta_id=pregunta_id,
        texto=body.texto,
        unidad_tematica=body.unidad_tematica,
        tema=body.tema,
        dificultad=body.dificultad,
        importancia=body.importancia,
        opciones=(
            [(o.texto, o.es_correcta) for o in body.opciones] if body.opciones is not None else None
        ),
        respuesta_correcta=body.respuesta_correcta,
        docente_id=usuario.usuario_id,
    )


@router.delete(
    "/{pregunta_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_docente)],
)
async def eliminar_pregunta(
    pregunta_id: UUID,
    usuario: JWTPayload = Depends(get_current_user),
    controller: PreguntasController = Depends(get_preguntas_controller),
) -> None:
    """Elimina (baja lógica) una pregunta existente.

    La fila persiste con `activa = false` — no se borra físicamente (INV-BP-04).
    Responde 404 si la pregunta no existe, 409 si ya estaba eliminada, 403 si el Docente no
    tiene ninguna Comisión asignada en la materia del banco de la pregunta (`US-ADJ-57`).
    """
    await controller.eliminar_pregunta(pregunta_id=pregunta_id, docente_id=usuario.usuario_id)
