"""Router FastAPI de administración de cuentas de usuario (RF-03)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from src.identidad.frameworks.api.schemas import CuentaResponse
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
