"""Controller de la API para la administración de cuentas de usuario (RF-03)."""

from __future__ import annotations

from uuid import UUID

from src.identidad.entities.resultado_paginado_cuentas import ResultadoPaginadoCuentas
from src.identidad.entities.usuario import Usuario
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
    ) -> None:
        """Recibe los casos de uso de listado, detalle y reseteo de cuentas a usar."""
        self._listar_cuentas = listar_cuentas
        self._obtener_cuenta = obtener_cuenta
        self._resetear_password = resetear_password

    async def listar_cuentas(
        self,
        rol: TipoPerfil | None,
        estado: str | None,
        busqueda: str | None,
        pagina: int = 1,
        tamanio_pagina: int = 20,
    ) -> ResultadoPaginadoCuentas:
        """Delega el listado filtrado y paginado en el caso de uso correspondiente."""
        return await self._listar_cuentas.execute(rol, estado, busqueda, pagina, tamanio_pagina)

    async def obtener_cuenta(self, usuario_id: UUID) -> Usuario:
        """Delega el detalle de una cuenta puntual en el caso de uso correspondiente."""
        return await self._obtener_cuenta.execute(usuario_id)

    async def resetear_password(
        self, usuario_id: UUID, password_nueva: str, administrador_id: UUID
    ) -> Usuario:
        """Delega el reseteo de contraseña en el caso de uso correspondiente.

        Devuelve solo la cuenta actualizada — el router decide qué exponer al cliente.
        """
        usuario, _evento_password, _evento_desbloqueo = await self._resetear_password.execute(
            usuario_id, password_nueva, administrador_id
        )
        return usuario
