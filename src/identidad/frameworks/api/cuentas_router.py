"""Router FastAPI de administración de cuentas de usuario (RF-03)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.identidad.entities.errors import PasswordDemasiadoCorta, UsuarioNoExiste
from src.identidad.entities.usuario import Estudiante, Usuario
from src.identidad.frameworks.api.schemas import (
    CuentaDetalleResponse,
    CuentaResponse,
    ResetearPasswordRequest,
)
from src.identidad.frameworks.dependencies import get_cuentas_controller, require_administrador
from src.identidad.interface_adapters.controllers.cuentas_controller import CuentasController
from src.shared.entities.jwt import JWTPayload
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

    return _a_detalle_response(usuario)


@router.post(
    "/{usuario_id}/resetear-password",
    response_model=CuentaDetalleResponse,
)
async def resetear_password(
    usuario_id: UUID,
    body: ResetearPasswordRequest,
    administrador: JWTPayload = Depends(require_administrador),
    controller: CuentasController = Depends(get_cuentas_controller),
) -> CuentaDetalleResponse:
    """Resetea la contraseña de una cuenta y la desbloquea si estaba bloqueada.

    Responde 404 si la cuenta no existe, 422 si la contraseña no cumple INV-ID-11.
    """
    try:
        usuario = await controller.resetear_password(
            usuario_id, body.password_nueva, administrador.usuario_id
        )
    except UsuarioNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PasswordDemasiadoCorta as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    return _a_detalle_response(usuario)


def _a_detalle_response(usuario: Usuario) -> CuentaDetalleResponse:
    """Arma el `CuentaDetalleResponse` a partir de un `Usuario`, resolviendo `comision_id`."""
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
