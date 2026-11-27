"""Controller de la API para la administración de cuentas de usuario (RF-03)."""

from __future__ import annotations

from uuid import UUID

from src.identidad.interface_adapters.presenters.identidad_presenter import (
    CuentaDetalleSalida,
    CuentasPaginadasSalida,
    presentar_cuenta_detalle,
    presentar_cuentas_paginadas,
)
from src.identidad.use_cases.activar_cuenta import ActivarCuentaUseCase
from src.identidad.use_cases.editar_cuenta import EditarCuentaUseCase
from src.identidad.use_cases.eliminar_cuenta import EliminarCuentaUseCase
from src.identidad.use_cases.listar_cuentas import ListarCuentasUseCase
from src.identidad.use_cases.obtener_cuenta import ObtenerCuentaUseCase
from src.identidad.use_cases.resetear_password import ResetearPasswordUseCase
from src.shared.entities.tipo_perfil import TipoPerfil


class CuentasController:
    """Adapta requests HTTP a los casos de uso de administración de cuentas."""

    def __init__(
        self,
        listar_cuentas: ListarCuentasUseCase,
        obtener_cuenta: ObtenerCuentaUseCase,
        resetear_password: ResetearPasswordUseCase,
        editar_cuenta: EditarCuentaUseCase,
        eliminar_cuenta: EliminarCuentaUseCase,
        activar_cuenta: ActivarCuentaUseCase,
    ) -> None:
        """Recibe los casos de uso de listado, detalle, reseteo, edición, baja y reactivación."""
        self._listar_cuentas = listar_cuentas
        self._obtener_cuenta = obtener_cuenta
        self._resetear_password = resetear_password
        self._editar_cuenta = editar_cuenta
        self._eliminar_cuenta = eliminar_cuenta
        self._activar_cuenta = activar_cuenta

    async def listar_cuentas(
        self,
        rol: TipoPerfil | None,
        estado: str | None,
        busqueda: str | None,
        pagina: int = 1,
        tamanio_pagina: int = 20,
        incluir_inactivas: bool = False,
    ) -> CuentasPaginadasSalida:
        """Delega el listado filtrado y paginado en el caso de uso correspondiente."""
        return presentar_cuentas_paginadas(
            await self._listar_cuentas.execute(
                rol, estado, busqueda, pagina, tamanio_pagina, incluir_inactivas
            )
        )

    async def obtener_cuenta(self, usuario_id: UUID) -> CuentaDetalleSalida:
        """Delega el detalle de una cuenta puntual en el caso de uso correspondiente."""
        return presentar_cuenta_detalle(await self._obtener_cuenta.execute(usuario_id))

    async def resetear_password(
        self, usuario_id: UUID, password_nueva: str, administrador_id: UUID
    ) -> CuentaDetalleSalida:
        """Resetea la contraseña y presenta la cuenta actualizada; los eventos se descartan acá."""
        usuario, _evento_password, _evento_desbloqueo = await self._resetear_password.execute(
            usuario_id, password_nueva, administrador_id
        )
        return presentar_cuenta_detalle(usuario)

    async def editar_cuenta(self, usuario_id: UUID, nombre: str, email: str) -> CuentaDetalleSalida:
        """Delega la corrección de nombre/email de una cuenta en el caso de uso correspondiente."""
        return presentar_cuenta_detalle(
            await self._editar_cuenta.execute(usuario_id, nombre, email)
        )

    async def eliminar_cuenta(self, usuario_id: UUID) -> CuentaDetalleSalida | None:
        """Delega la baja (física o lógica) de una cuenta en el caso de uso correspondiente."""
        resultado = await self._eliminar_cuenta.execute(usuario_id)
        return None if resultado is None else presentar_cuenta_detalle(resultado)

    async def activar_cuenta(self, usuario_id: UUID) -> CuentaDetalleSalida:
        """Delega la reactivación de una cuenta deshabilitada en el caso de uso correspondiente."""
        return presentar_cuenta_detalle(await self._activar_cuenta.execute(usuario_id))
