"""Router FastAPI de autoregistro de cuentas sin invitación (`US-ADJ-41`/`42`/`43`)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.identidad.entities.errors import (
    ComisionNoExiste,
    EmailYaRegistrado,
    PasswordDemasiadoCorta,
    PasswordSinComplejidadSuficiente,
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

router = APIRouter(prefix="/identidad/autoregistro", tags=["identidad"])


@router.post("/docente", response_model=AutoregistroResponse, status_code=status.HTTP_201_CREATED)
async def autoregistrar_docente(
    body: AutoregistrarDocenteRequest,
    controller: AutoregistroController = Depends(get_autoregistro_controller),
) -> AutoregistroResponse:
    """Crea una cuenta de Docente activa de inmediato; endpoint público, sin JWT.

    Responde 409 si el email ya está registrado, o 422 si `password` no cumple INV-ID-11
    (ampliada, `US-ADJ-36`).
    """
    try:
        usuario, _evento = await controller.autoregistrar_docente(
            body.nombre, body.email, body.password
        )
    except EmailYaRegistrado as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except (PasswordDemasiadoCorta, PasswordSinComplejidadSuficiente) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    return AutoregistroResponse(
        id=usuario.id,
        nombre=usuario.nombre,
        email=usuario.email,
        tipo_perfil=usuario.tipo_perfil.value,
    )


@router.get("/materias", response_model=list[MateriaAutoregistroResponse])
async def listar_materias_autoregistro(
    controller: AutoregistroController = Depends(get_autoregistro_controller),
) -> list[MateriaAutoregistroResponse]:
    """Lista las materias para el selector de la pantalla de autoregistro de Estudiante.

    Endpoint público, sin JWT (`US-ADJ-43`) — quien se autoregistra todavía no tiene cuenta,
    no puede llamar `GET /materias` (`US-2.1.9`, exige rol `docente`/`administrador`). Expone
    solo `id`/`nombre`, sin los campos adicionales de ese endpoint protegido.
    """
    materias = await controller.listar_materias()
    return [
        MateriaAutoregistroResponse(id=materia.id, nombre=materia.nombre) for materia in materias
    ]


@router.get("/materias/{materia_id}/comisiones", response_model=list[ComisionAutoregistroResponse])
async def listar_comisiones_autoregistro(
    materia_id: UUID,
    controller: AutoregistroController = Depends(get_autoregistro_controller),
) -> list[ComisionAutoregistroResponse]:
    """Lista las comisiones activas de una materia para el mismo selector.

    Endpoint público, sin JWT (`US-ADJ-43`) — mismo motivo que `listar_materias_autoregistro`.
    Materia inexistente o sin comisiones → lista vacía (no distingue, mismo criterio que
    `ComisionQueryPort.listar_comisiones_por_materia`).
    """
    comisiones = await controller.listar_comisiones_por_materia(materia_id)
    return [
        ComisionAutoregistroResponse(id=comision.id, horario=comision.horario)
        for comision in comisiones
    ]


@router.post(
    "/estudiante", response_model=AutoregistroResponse, status_code=status.HTTP_201_CREATED
)
async def autoregistrar_estudiante(
    body: AutoregistrarEstudianteRequest,
    controller: AutoregistroController = Depends(get_autoregistro_controller),
) -> AutoregistroResponse:
    """Crea una cuenta de Estudiante activa de inmediato; endpoint público, sin JWT.

    Responde 409 si el email ya está registrado, 422 si `comision_id` no existe
    (`ComisionNoExiste`, INV-ID-14) o si `password` no cumple INV-ID-11 (ampliada, `US-ADJ-36`).
    """
    try:
        usuario, _evento = await controller.autoregistrar_estudiante(
            body.nombre, body.email, body.password, body.comision_id
        )
    except EmailYaRegistrado as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ComisionNoExiste as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    except (PasswordDemasiadoCorta, PasswordSinComplejidadSuficiente) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    return AutoregistroResponse(
        id=usuario.id,
        nombre=usuario.nombre,
        email=usuario.email,
        tipo_perfil=usuario.tipo_perfil.value,
    )
