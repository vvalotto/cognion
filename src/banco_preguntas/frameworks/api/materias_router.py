"""Router FastAPI de operaciones sobre materias."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.banco_preguntas.entities.errors import MateriaYaExiste
from src.banco_preguntas.frameworks.api.schemas import CrearMateriaRequest, MateriaResponse
from src.banco_preguntas.frameworks.dependencies import get_materias_controller, require_docente
from src.banco_preguntas.interface_adapters.controllers.materias_controller import (
    MateriasController,
)

router = APIRouter(prefix="/materias", tags=["banco_preguntas"])


@router.post(
    "",
    response_model=MateriaResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_docente)],
)
async def crear_materia(
    body: CrearMateriaRequest,
    controller: MateriasController = Depends(get_materias_controller),
) -> MateriaResponse:
    """Crea una materia nueva y su banco asociado; responde 409 si el nombre ya existe."""
    try:
        materia, banco, _evento_materia, _evento_banco = await controller.crear_materia(body.nombre)
    except MateriaYaExiste as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return MateriaResponse(id=materia.id, nombre=materia.nombre, banco_id=banco.id)
