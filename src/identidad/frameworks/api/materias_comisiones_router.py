"""Router FastAPI de consultas de comisiones de una materia (`US-4.2.2`).

Prefijo `/materias` propio de Identidad — coexiste sin colisión con
`src/banco_preguntas/frameworks/api/materias_router.py` (mismo prefijo, paths distintos:
`POST /materias`, `GET /materias` allá; `GET /materias/{id}/comisiones` acá). El alias de
import en `app.py` debe ser distinto al de ese router.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.identidad.entities.errors import MateriaNoExiste
from src.identidad.frameworks.api.schemas import ComisionResumenResponse
from src.identidad.frameworks.dependencies import get_comisiones_query_controller, require_docente
from src.identidad.interface_adapters.controllers.comisiones_query_controller import (
    ComisionesQueryController,
)

router = APIRouter(prefix="/materias", tags=["identidad"])


@router.get(
    "/{materia_id}/comisiones",
    response_model=list[ComisionResumenResponse],
    dependencies=[Depends(require_docente)],
)
async def listar_comisiones_por_materia(
    materia_id: UUID,
    controller: ComisionesQueryController = Depends(get_comisiones_query_controller),
) -> list[ComisionResumenResponse]:
    """Comisiones de la materia; 404 si `materia_id` no existe (`US-4.2.2`)."""
    try:
        comisiones = await controller.listar_comisiones_por_materia(materia_id)
    except MateriaNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [ComisionResumenResponse(id=c.id, horario=c.horario) for c in comisiones]
