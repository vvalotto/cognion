"""Router FastAPI de autoregistro de cuentas sin invitación (`US-ADJ-41`/`42`/`43`)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.identidad.entities.errors import (
    ComisionNoExiste,
)
from src.identidad.frameworks.api.schemas import (
    AutoregistrarDocenteRequest,
    AutoregistrarEstudianteRequest,
    AutoregistroResponse,
    ComisionAutoregistroResponse,
    MateriaAutoregistroResponse,
)
from src.identidad.frameworks.dependencies import get_autoregistro_controller
from src.identidad.interface_adapters.controllers.autoregistro_controller import (
    AutoregistroController,
)
from src.identidad.interface_adapters.presenters.identidad_presenter import (
    AutoregistroSalida,
    ComisionAutoregistroSalida,
    MateriaAutoregistroSalida,
)

router = APIRouter(prefix="/identidad/autoregistro", tags=["identidad"])


@router.post("/docente", response_model=AutoregistroResponse, status_code=status.HTTP_201_CREATED)
async def autoregistrar_docente(
    body: AutoregistrarDocenteRequest,
    controller: AutoregistroController = Depends(get_autoregistro_controller),
) -> AutoregistroSalida:
    """Crea una cuenta de Docente activa de inmediato; endpoint público, sin JWT.

    Responde 409 si el email ya está registrado, o 422 si `password` no cumple INV-ID-11
    (ampliada, `US-ADJ-36`).
    """
    return await controller.autoregistrar_docente(body.nombre, body.email, body.password)


@router.get("/materias", response_model=list[MateriaAutoregistroResponse])
async def listar_materias_autoregistro(
    controller: AutoregistroController = Depends(get_autoregistro_controller),
) -> list[MateriaAutoregistroSalida]:
    """Lista las materias para el selector de la pantalla de autoregistro de Estudiante.

    Endpoint público, sin JWT (`US-ADJ-43`) — quien se autoregistra todavía no tiene cuenta,
    no puede llamar `GET /materias` (`US-2.1.9`, exige rol `docente`/`administrador`). Expone
    solo `id`/`nombre`, sin los campos adicionales de ese endpoint protegido.
    """
    return await controller.listar_materias()


@router.get("/materias/{materia_id}/comisiones", response_model=list[ComisionAutoregistroResponse])
async def listar_comisiones_autoregistro(
    materia_id: UUID,
    controller: AutoregistroController = Depends(get_autoregistro_controller),
) -> list[ComisionAutoregistroSalida]:
    """Lista las comisiones activas de una materia para el mismo selector.

    Endpoint público, sin JWT (`US-ADJ-43`) — mismo motivo que `listar_materias_autoregistro`.
    Materia inexistente o sin comisiones → lista vacía (no distingue, mismo criterio que
    `ComisionQueryPort.listar_comisiones_por_materia`).
    """
    return await controller.listar_comisiones_por_materia(materia_id)


@router.post(
    "/estudiante", response_model=AutoregistroResponse, status_code=status.HTTP_201_CREATED
)
async def autoregistrar_estudiante(
    body: AutoregistrarEstudianteRequest,
    controller: AutoregistroController = Depends(get_autoregistro_controller),
) -> AutoregistroSalida:
    """Crea una cuenta de Estudiante activa de inmediato; endpoint público, sin JWT.

    Responde 409 si el email ya está registrado, 422 si `comision_id` no existe
    (`ComisionNoExiste`, INV-ID-14) o si `password` no cumple INV-ID-11 (ampliada, `US-ADJ-36`).
    """
    try:
        return await controller.autoregistrar_estudiante(
            body.nombre, body.email, body.password, body.comision_id
        )
    except ComisionNoExiste as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
