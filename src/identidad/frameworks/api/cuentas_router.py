"""Router FastAPI de administración de cuentas de usuario (RF-03)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from src.identidad.frameworks.api.schemas import (
    CuentaDetalleResponse,
    CuentasPaginadasResponse,
    EditarCuentaRequest,
    ResetearPasswordRequest,
)
from src.identidad.frameworks.dependencies import get_cuentas_controller, require_administrador
from src.identidad.interface_adapters.controllers.cuentas_controller import CuentasController
from src.identidad.interface_adapters.presenters.identidad_presenter import (
    CuentaDetalleSalida,
    CuentasPaginadasSalida,
)
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
    pagina: int = Query(1, ge=1),
    tamanio_pagina: int = Query(20, ge=1),
    incluir_inactivas: bool = False,
    controller: CuentasController = Depends(get_cuentas_controller),
) -> CuentasPaginadasSalida:
    """Lista cuentas filtradas (AND) por rol, estado (`activa`/`bloqueada`/`inactiva`) y búsqueda.

    Página fija de `tamanio_pagina` (default 20), orden estable por `creado_en`.
    `incluir_inactivas=True` también trae las cuentas deshabilitadas — lo usa la pantalla de
    gestión de Cuentas; el resto de los consumidores (selectores de Docentes) sigue viendo
    solo las habilitadas.
    """
    return await controller.listar_cuentas(
        rol, estado, busqueda, pagina, tamanio_pagina, incluir_inactivas
    )


@router.get(
    "/{usuario_id}",
    response_model=CuentaDetalleResponse,
    dependencies=[Depends(require_administrador)],
)
async def obtener_cuenta(
    usuario_id: UUID,
    controller: CuentasController = Depends(get_cuentas_controller),
) -> CuentaDetalleSalida:
    """Detalle de una cuenta puntual; responde 404 si no existe."""
    return await controller.obtener_cuenta(usuario_id)


@router.post(
    "/{usuario_id}/resetear-password",
    response_model=CuentaDetalleResponse,
)
async def resetear_password(
    usuario_id: UUID,
    body: ResetearPasswordRequest,
    administrador: JWTPayload = Depends(require_administrador),
    controller: CuentasController = Depends(get_cuentas_controller),
) -> CuentaDetalleSalida:
    """Resetea la contraseña de una cuenta y la desbloquea si estaba bloqueada.

    Responde 404 si la cuenta no existe, 422 si la contraseña no cumple INV-ID-11.
    """
    return await controller.resetear_password(
        usuario_id, body.password_nueva, administrador.usuario_id
    )


@router.patch(
    "/{usuario_id}",
    response_model=CuentaDetalleResponse,
    dependencies=[Depends(require_administrador)],
)
async def editar_cuenta(
    usuario_id: UUID,
    body: EditarCuentaRequest,
    controller: CuentasController = Depends(get_cuentas_controller),
) -> CuentaDetalleSalida:
    """Corrige nombre/email de una cuenta existente — no toca password, bloqueo ni perfil.

    Responde 404 si la cuenta no existe, 409 si el email nuevo ya pertenece a otra cuenta.
    """
    return await controller.editar_cuenta(usuario_id, body.nombre, body.email)


@router.delete(
    "/{usuario_id}",
    response_model=None,
    dependencies=[Depends(require_administrador)],
)
async def eliminar_cuenta(
    usuario_id: UUID,
    controller: CuentasController = Depends(get_cuentas_controller),
) -> CuentaDetalleSalida | Response:
    """Borra la cuenta, o la deshabilita si tiene datos asociados (Comisiones, evaluaciones).

    204 si se borró físicamente; 200 con la cuenta (`deshabilitada=true`) si se deshabilitó.
    Un Administrador siempre se deshabilita (nunca se borra). 404 si la cuenta no existe; 409 con
    `detail.codigo = "ultimo_administrador_operativo"` si es el único Administrador operativo.
    """
    usuario = await controller.eliminar_cuenta(usuario_id)

    if usuario is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return usuario


@router.post(
    "/{usuario_id}/activar",
    response_model=CuentaDetalleResponse,
    dependencies=[Depends(require_administrador)],
)
async def activar_cuenta(
    usuario_id: UUID,
    controller: CuentasController = Depends(get_cuentas_controller),
) -> CuentaDetalleSalida:
    """Reactiva una cuenta deshabilitada; 404 si no existe."""
    return await controller.activar_cuenta(usuario_id)
