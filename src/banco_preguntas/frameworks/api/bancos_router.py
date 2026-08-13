"""Router FastAPI de operaciones de consulta sobre bancos."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.banco_preguntas.entities.errors import BancoNoExiste
from src.banco_preguntas.entities.pregunta_plantilla import PreguntaPlantillaOpcionMultiple
from src.banco_preguntas.frameworks.api.schemas import (
    PreguntaOpcionMultipleResponse,
    PreguntaVerdaderoFalsoResponse,
)
from src.banco_preguntas.frameworks.dependencies import get_bancos_controller, require_docente
from src.banco_preguntas.interface_adapters.controllers.bancos_controller import (
    BancosController,
)

router = APIRouter(prefix="/bancos", tags=["banco_preguntas"])


@router.get(
    "/{banco_id}/preguntas",
    response_model=list[PreguntaOpcionMultipleResponse | PreguntaVerdaderoFalsoResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_docente)],
)
async def filtrar_preguntas(
    banco_id: UUID,
    unidad: str | None = None,
    tema: str | None = None,
    dificultad: str | None = None,
    importancia: str | None = None,
    controller: BancosController = Depends(get_bancos_controller),
) -> list[PreguntaOpcionMultipleResponse | PreguntaVerdaderoFalsoResponse]:
    """Filtra las preguntas activas del banco por cualquier combinación de metadatos.

    Los filtros son opcionales y combinables (AND). Responde 404 si el banco no existe.
    """
    try:
        preguntas = await controller.filtrar_preguntas(
            banco_id=banco_id,
            unidad=unidad,
            tema=tema,
            dificultad=dificultad,
            importancia=importancia,
        )
    except BancoNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [
        (
            PreguntaOpcionMultipleResponse(
                id=pregunta.id,
                banco_id=pregunta.banco_id,
                texto=pregunta.texto,
                opciones=[
                    {"texto": o.texto, "es_correcta": o.es_correcta} for o in pregunta.opciones
                ],
                unidad_tematica=pregunta.unidad_tematica,
                tema=pregunta.tema,
                dificultad=pregunta.dificultad,
                importancia=pregunta.importancia,
                activa=pregunta.activa,
            )
            if isinstance(pregunta, PreguntaPlantillaOpcionMultiple)
            else PreguntaVerdaderoFalsoResponse(
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
        )
        for pregunta in preguntas
    ]
