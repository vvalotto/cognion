"""Router FastAPI de operaciones sobre materias."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.banco_preguntas.entities.errors import MateriaNoExiste, MateriaYaExiste
from src.banco_preguntas.frameworks.api.schemas import (
    CrearMateriaRequest,
    EditarMateriaRequest,
    MateriaBasicaResponse,
    MateriaListItemResponse,
    MateriaResponse,
)
from src.banco_preguntas.frameworks.dependencies import (
    get_materias_controller,
    require_docente_o_administrador,
)
from src.banco_preguntas.interface_adapters.controllers.materias_controller import (
    MateriasController,
)

router = APIRouter(prefix="/materias", tags=["banco_preguntas"])


@router.post(
    "",
    response_model=MateriaResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_docente_o_administrador)],
)
async def crear_materia(
    body: CrearMateriaRequest,
    controller: MateriasController = Depends(get_materias_controller),
) -> MateriaResponse:
    """Crea una materia nueva y su banco asociado; responde 409 si el nombre ya existe.

    Rol `docente` o `administrador` (hallazgo de la prueba manual E2E: sin ninguna Materia
    creada, el Administrador no tenía forma de crear la Comisión que la referencia).
    """
    try:
        materia, banco, _evento_materia, _evento_banco = await controller.crear_materia(body.nombre)
    except MateriaYaExiste as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return MateriaResponse(id=materia.id, nombre=materia.nombre, banco_id=banco.id)


@router.patch(
    "/{materia_id}",
    response_model=MateriaBasicaResponse,
    dependencies=[Depends(require_docente_o_administrador)],
)
async def editar_materia(
    materia_id: UUID,
    body: EditarMateriaRequest,
    controller: MateriasController = Depends(get_materias_controller),
) -> MateriaBasicaResponse:
    """Corrige el nombre de una materia existente.

    Rol `docente` o `administrador` — hallazgo de la prueba manual E2E: no existía forma de
    corregir un nombre cargado con error de tipeo, para ningún rol. Responde 404 si la
    materia no existe, 409 si el nombre nuevo ya pertenece a otra.
    """
    try:
        materia = await controller.editar_materia(materia_id, body.nombre)
    except MateriaNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except MateriaYaExiste as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return MateriaBasicaResponse(id=materia.id, nombre=materia.nombre)


@router.get(
    "",
    response_model=list[MateriaListItemResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_docente_o_administrador)],
)
async def listar_materias(
    controller: MateriasController = Depends(get_materias_controller),
) -> list[MateriaListItemResponse]:
    """Lista todas las materias con la cantidad de preguntas activas de cada una.

    Rol `docente` o `administrador` (`US-ADJ-23`, gap detectado en Fase 3).
    """
    materias = await controller.listar_materias()
    return [
        MateriaListItemResponse(
            id=materia.id,
            nombre=materia.nombre,
            banco_id=banco.id,
            cantidad_preguntas_activas=cantidad,
        )
        for materia, banco, cantidad in materias
    ]
