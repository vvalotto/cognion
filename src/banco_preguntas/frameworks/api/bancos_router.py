"""Router FastAPI de operaciones de consulta sobre bancos."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.banco_preguntas.frameworks.api.schemas import PreguntasPaginadasResponse
from src.banco_preguntas.frameworks.dependencies import (
    get_bancos_controller,
    get_current_user,
    require_docente,
)
from src.banco_preguntas.interface_adapters.controllers.bancos_controller import (
    BancosController,
)
from src.banco_preguntas.interface_adapters.presenters.banco_presenter import (
    PreguntasPaginadasSalida,
)
from src.shared.entities.jwt import JWTPayload

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
    pagina: int | None = Query(None, ge=1),
    tamanio_pagina: int | None = Query(None, ge=1),
    usuario: JWTPayload = Depends(get_current_user),
    controller: BancosController = Depends(get_bancos_controller),
) -> PreguntasPaginadasSalida:
    """Filtra las preguntas activas del banco por cualquier combinación de metadatos.

    Los filtros son opcionales y combinables (AND). `pagina`/`tamanio_pagina` son opt-in
    (US-ADJ-03): si se omite alguno, la respuesta trae todas las preguntas que matchean, sin
    paginar — mismo comportamiento que antes de esta US. Responde 404 si el banco no existe,
    403 si el Docente no tiene ninguna Comisión asignada en la materia del banco (`US-ADJ-57`).
    """
    return await controller.filtrar_preguntas(
        banco_id=banco_id,
        unidad=unidad,
        tema=tema,
        dificultad=dificultad,
        importancia=importancia,
        pagina=pagina,
        tamanio_pagina=tamanio_pagina,
        docente_id=usuario.usuario_id,
    )
