"""Router FastAPI de administración de cuentas de usuario (RF-03)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.identidad.entities.errors import UsuarioNoExiste
from src.identidad.entities.usuario import Estudiante
from src.identidad.frameworks.api.schemas import CuentaDetalleResponse, CuentaResponse
from src.identidad.frameworks.dependencies import get_cuentas_controller, require_administrador
from src.identidad.interface_adapters.controllers.cuentas_controller import CuentasController
from src.shared.entities.tipo_perfil import TipoPerfil

router = APIRouter(prefix="/usuarios", tags=["identidad"])


@router.get(
    "",
    response_model=list[CuentaResponse],
    dependencies=[Depends(require_administrador)],
)
async def listar_cuentas(
    rol: TipoPerfil | None = None,
    estado: str | None = None,
    busqueda: str | None = None,
    controller: CuentasController = Depends(get_cuentas_controller),
) -> list[CuentaResponse]:
    """Lista cuentas filtradas (AND) por rol, estado (`activa`/`bloqueada`) y búsqueda."""
    usuarios = await controller.listar_cuentas(rol, estado, busqueda)
    return [
        CuentaResponse(
            id=usuario.id,
            nombre=usuario.nombre,
            email=usuario.email,
            perfil=usuario.tipo_perfil,
            bloqueada=usuario.bloqueada,
        )
        for usuario in usuarios
    ]


@router.get(
    "/{usuario_id}",
    response_model=CuentaDetalleResponse,
    dependencies=[Depends(require_administrador)],
)
async def obtener_cuenta(
    usuario_id: UUID,
    controller: CuentasController = Depends(get_cuentas_controller),
) -> CuentaDetalleResponse:
    """Detalle de una cuenta puntual; responde 404 si no existe."""
    try:
        usuario = await controller.obtener_cuenta(usuario_id)
    except UsuarioNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    comision_id = usuario.perfil.comision_id if isinstance(usuario.perfil, Estudiante) else None
    return CuentaDetalleResponse(
        id=usuario.id,
        nombre=usuario.nombre,
        email=usuario.email,
        perfil=usuario.tipo_perfil,
        bloqueada=usuario.bloqueada,
        creado_en=usuario.creado_en,
        comision_id=comision_id,
    )
