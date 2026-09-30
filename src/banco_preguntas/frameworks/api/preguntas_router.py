"""Router FastAPI de operaciones sobre preguntas."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.banco_preguntas.entities.errors import (
    BancoNoExiste,
    MateriaNoAutorizada,
    OpcionesInvalidas,
    PreguntaInactiva,
    PreguntaNoExiste,
    PreguntaYaEliminada,
)
from src.banco_preguntas.entities.metadatos_pregunta import MetadatosPregunta
from src.banco_preguntas.entities.opcion import Opcion
from src.banco_preguntas.entities.pregunta_plantilla import PreguntaPlantillaOpcionMultiple
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
) -> PreguntaOpcionMultipleResponse:
    """Carga una pregunta de opción múltiple.

    Responde 404 si el banco no existe, 422 si las opciones son inválidas, 403 si el Docente
    no tiene ninguna Comisión asignada en la materia del banco (`US-ADJ-57`).
    """
    try:
        pregunta, _evento = await controller.cargar_pregunta_opcion_multiple(
            banco_id=body.banco_id,
            metadatos=MetadatosPregunta(
                texto=body.texto,
                unidad_tematica=body.unidad_tematica,
                tema=body.tema,
                dificultad=body.dificultad,
                importancia=body.importancia,
            ),
            opciones=[Opcion(texto=o.texto, es_correcta=o.es_correcta) for o in body.opciones],
            docente_id=usuario.usuario_id,
        )
    except BancoNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except OpcionesInvalidas as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    except MateriaNoAutorizada as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

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
    usuario: JWTPayload = Depends(get_current_user),
    controller: PreguntasController = Depends(get_preguntas_controller),
) -> PreguntaVerdaderoFalsoResponse:
    """Carga una pregunta Verdadero/Falso.

    Responde 404 si el banco no existe, 403 si el Docente no tiene ninguna Comisión
    asignada en la materia del banco (`US-ADJ-57`).
    """
    try:
        pregunta, _evento = await controller.cargar_pregunta_verdadero_falso(
            banco_id=body.banco_id,
            metadatos=MetadatosPregunta(
                texto=body.texto,
                unidad_tematica=body.unidad_tematica,
                tema=body.tema,
                dificultad=body.dificultad,
                importancia=body.importancia,
            ),
            respuesta_correcta=body.respuesta_correcta,
            docente_id=usuario.usuario_id,
        )
    except BancoNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except MateriaNoAutorizada as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

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
) -> PreguntaOpcionMultipleResponse | PreguntaVerdaderoFalsoResponse:
    """Edita una pregunta existente (texto, opciones/respuesta, metadatos).

    El tipo de la pregunta (Opción Múltiple / Verdadero-Falso) no es editable.
    Responde 404 si la pregunta no existe, 409 si está inactiva, 422 si las opciones editadas
    son inválidas, 403 si el Docente no tiene ninguna Comisión asignada en la materia del
    banco de la pregunta (`US-ADJ-57`).
    """
    try:
        pregunta, _evento = await controller.editar_pregunta(
            pregunta_id=pregunta_id,
            metadatos=MetadatosPregunta(
                texto=body.texto,
                unidad_tematica=body.unidad_tematica,
                tema=body.tema,
                dificultad=body.dificultad,
                importancia=body.importancia,
            ),
            opciones=(
                [Opcion(texto=o.texto, es_correcta=o.es_correcta) for o in body.opciones]
                if body.opciones is not None
                else None
            ),
            respuesta_correcta=body.respuesta_correcta,
            docente_id=usuario.usuario_id,
        )
    except PreguntaNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PreguntaInactiva as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except OpcionesInvalidas as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    except MateriaNoAutorizada as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    if isinstance(pregunta, PreguntaPlantillaOpcionMultiple):
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
    try:
        await controller.eliminar_pregunta(pregunta_id=pregunta_id, docente_id=usuario.usuario_id)
    except PreguntaNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PreguntaYaEliminada as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except MateriaNoAutorizada as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
