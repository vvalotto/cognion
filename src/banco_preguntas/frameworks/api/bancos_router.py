"""Router FastAPI de operaciones de consulta sobre bancos."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.banco_preguntas.entities.errors import BancoNoExiste
from src.banco_preguntas.entities.pregunta_plantilla import PreguntaPlantillaOpcionMultiple
from src.banco_preguntas.frameworks.api.schemas import (
    PreguntaOpcionMultipleResponse,
    PreguntasPaginadasResponse,
    PreguntaVerdaderoFalsoResponse,
)
from src.banco_preguntas.frameworks.dependencies import get_bancos_controller, require_docente
from src.banco_preguntas.interface_adapters.controllers.bancos_controller import (
    BancosController,
)

router = APIRouter(prefix="/bancos", tags=["banco_preguntas"])


@router.get(
    "/{banco_id}/preguntas",
    response_model=PreguntasPaginadasResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_docente)],
)
async def filtrar_preguntas(
    banco_id: UUID,
    unidad: str | None = None,
    tema: str | None = None,
    dificultad: str | None = None,
    importancia: str | None = None,
    pagina: int | None = None,
    tamanio_pagina: int | None = None,
    controller: BancosController = Depends(get_bancos_controller),
) -> PreguntasPaginadasResponse:
    """Filtra las preguntas activas del banco por cualquier combinación de metadatos.

    Los filtros son opcionales y combinables (AND). `pagina`/`tamanio_pagina` son opt-in
    (US-ADJ-03): si se omite alguno, la respuesta trae todas las preguntas que matchean, sin
    paginar — mismo comportamiento que antes de esta US. Responde 404 si el banco no existe.
    """
    try:
        resultado = await controller.filtrar_preguntas(
            banco_id=banco_id,
            unidad=unidad,
            tema=tema,
            dificultad=dificultad,
            importancia=importancia,
            pagina=pagina,
            tamanio_pagina=tamanio_pagina,
        )
    except BancoNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return PreguntasPaginadasResponse(
        preguntas=[
            (
                PreguntaOpcionMultipleResponse(
                    id=pregunta.id,
                    banco_id=pregunta.banco_id,
                    texto=pregunta.texto,
                    opciones=[
                        {"texto": o.texto, "es_correcta": o.es_correcta}
                        for o in pregunta.opciones
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
            for pregunta in resultado.preguntas
        ],
        total=resultado.total,
    )
