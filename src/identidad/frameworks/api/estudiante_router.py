"""Router FastAPI de acciones de autoservicio del Estudiante (RF-11)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from src.identidad.frameworks.api.schemas import MateriaEstudianteResponse
from src.identidad.frameworks.dependencies import (
    get_current_user,
    get_estudiante_controller,
    require_estudiante,
)
from src.identidad.interface_adapters.controllers.estudiante_controller import (
    EstudianteController,
)
from src.shared.entities.jwt import JWTPayload

router = APIRouter(prefix="/identidad/estudiante", tags=["identidad"])


@router.get(
    "/materias",
    response_model=list[MateriaEstudianteResponse],
    dependencies=[Depends(require_estudiante)],
)
async def listar_mis_materias(
    usuario: JWTPayload = Depends(get_current_user),
    controller: EstudianteController = Depends(get_estudiante_controller),
) -> list[MateriaEstudianteResponse]:
    """Devuelve la materia de la comisión del Estudiante autenticado."""
    materias = await controller.listar_mis_materias(usuario.usuario_id)
    return [MateriaEstudianteResponse(id=materia.id, nombre=materia.nombre) for materia in materias]
