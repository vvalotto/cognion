"""Router FastAPI de administración de cuentas de usuario (RF-03)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from src.identidad.entities.errors import (
    EmailYaRegistrado,
    PasswordDemasiadoCorta,
    PasswordSinComplejidadSuficiente,
    UsuarioNoExiste,
)
from src.identidad.entities.usuario import Estudiante, Usuario
from src.identidad.frameworks.api.schemas import (
    CuentaDetalleResponse,
    CuentaResponse,
    CuentasPaginadasResponse,
    EditarCuentaRequest,
    ResetearPasswordRequest,
)
from src.identidad.frameworks.dependencies import get_cuentas_controller, require_administrador
from src.identidad.interface_adapters.controllers.cuentas_controller import CuentasController
from src.shared.entities.jwt import JWTPayload
from src.shared.entities.tipo_perfil import TipoPerfil

router = APIRouter(prefix="/usuarios", tags=["identidad"])


@router.get(
    "",
    response_model=CuentasPaginadasResponse,
    dependencies=[Depends(require_administrador)],
)
async def listar_cuentas(
    rol: TipoPerfil | None = None,
    estado: str | None = None,
    busqueda: str | None = None,
    pagina: int = 1,
    tamanio_pagina: int = 20,
    incluir_inactivas: bool = False,
    controller: CuentasController = Depends(get_cuentas_controller),
) -> CuentasPaginadasResponse:
    """Lista cuentas filtradas (AND) por rol, estado (`activa`/`bloqueada`/`inactiva`) y búsqueda.

    Página fija de `tamanio_pagina` (default 20), orden estable por `creado_en`.
    `incluir_inactivas=True` también trae las cuentas deshabilitadas — lo usa la pantalla de
    gestión de Cuentas; el resto de los consumidores (selectores de Docentes) sigue viendo
    solo las habilitadas.
    """
    resultado = await controller.listar_cuentas(
        rol, estado, busqueda, pagina, tamanio_pagina, incluir_inactivas
    )
    return CuentasPaginadasResponse(
        cuentas=[
            CuentaResponse(
                id=usuario.id,
                nombre=usuario.nombre,
                email=usuario.email,
                perfil=usuario.tipo_perfil,
                bloqueada=usuario.bloqueada,
                deshabilitada=usuario.deshabilitada,
            )
            for usuario in resultado.cuentas
        ],
        total=resultado.total,
    )


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
    except (PasswordDemasiadoCorta, PasswordSinComplejidadSuficiente) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    return _a_detalle_response(usuario)


@router.patch(
    "/{usuario_id}",
    response_model=CuentaDetalleResponse,
    dependencies=[Depends(require_administrador)],
)
async def editar_cuenta(
    usuario_id: UUID,
    body: EditarCuentaRequest,
    controller: CuentasController = Depends(get_cuentas_controller),
) -> CuentaDetalleResponse:
    """Corrige nombre/email de una cuenta existente — no toca password, bloqueo ni perfil.

    Responde 404 si la cuenta no existe, 409 si el email nuevo ya pertenece a otra cuenta.
    """
    try:
        usuario = await controller.editar_cuenta(usuario_id, body.nombre, body.email)
    except UsuarioNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EmailYaRegistrado as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return _a_detalle_response(usuario)


@router.delete(
    "/{usuario_id}",
    response_model=None,
    dependencies=[Depends(require_administrador)],
)
async def eliminar_cuenta(
    usuario_id: UUID,
    controller: CuentasController = Depends(get_cuentas_controller),
) -> CuentaDetalleResponse | Response:
    """Borra la cuenta, o la deshabilita si tiene datos asociados (Comisiones, evaluaciones).

    204 si se borró físicamente; 200 con la cuenta (`deshabilitada=true`) si se deshabilitó.
    404 si la cuenta no existe.
    """
    try:
        usuario = await controller.eliminar_cuenta(usuario_id)
    except UsuarioNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    if usuario is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return _a_detalle_response(usuario)


@router.post(
    "/{usuario_id}/activar",
    response_model=CuentaDetalleResponse,
    dependencies=[Depends(require_administrador)],
)
async def activar_cuenta(
    usuario_id: UUID,
    controller: CuentasController = Depends(get_cuentas_controller),
) -> CuentaDetalleResponse:
    """Reactiva una cuenta deshabilitada; 404 si no existe."""
    try:
        usuario = await controller.activar_cuenta(usuario_id)
    except UsuarioNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

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
        deshabilitada=usuario.deshabilitada,
    )
