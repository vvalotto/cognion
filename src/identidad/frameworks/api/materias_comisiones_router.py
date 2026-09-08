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
from src.identidad.frameworks.dependencies import (
    get_comisiones_query_controller,
    require_docente_o_administrador,
)
from src.identidad.interface_adapters.controllers.comisiones_query_controller import (
    ComisionesQueryController,
)

router = APIRouter(prefix="/materias", tags=["identidad"])


@router.get(
    "/{materia_id}/comisiones",
    response_model=list[ComisionResumenResponse],
    dependencies=[Depends(require_docente_o_administrador)],
)
async def listar_comisiones_por_materia(
    materia_id: UUID,
    incluir_inactivas: bool = False,
    controller: ComisionesQueryController = Depends(get_comisiones_query_controller),
) -> list[ComisionResumenResponse]:
    """Comisiones de la materia, con sus docentes asignados.

    404 si `materia_id` no existe (`US-4.2.2`, `docentes_asignados` agregado en `US-ADJ-23`).
    `incluir_inactivas=True` también trae las deshabilitadas — lo usa la pantalla de gestión
    de Comisiones del Administrador; el resto de los consumidores sigue viendo solo las
    activas.
    """
    try:
        comisiones = await controller.listar_comisiones_por_materia(materia_id, incluir_inactivas)
    except MateriaNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [
        ComisionResumenResponse(
            id=c.id, horario=c.horario, docentes_asignados=c.docentes_asignados, activa=c.activa
        )
        for c in comisiones
    ]
