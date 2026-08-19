"""Controller de la API para la administración de cuentas de usuario (RF-03)."""

from __future__ import annotations

from uuid import UUID

from src.identidad.entities.usuario import Usuario
from src.identidad.use_cases.listar_cuentas import ListarCuentasUseCase
from src.identidad.use_cases.obtener_cuenta import ObtenerCuentaUseCase
from src.shared.entities.tipo_perfil import TipoPerfil


class CuentasController:
    """Adapta requests HTTP a los casos de uso de administración de cuentas."""

    def __init__(
        self, listar_cuentas: ListarCuentasUseCase, obtener_cuenta: ObtenerCuentaUseCase
    ) -> None:
        """Recibe los casos de uso de listado y detalle de cuentas a usar."""
        self._listar_cuentas = listar_cuentas
        self._obtener_cuenta = obtener_cuenta

    async def listar_cuentas(
        self, rol: TipoPerfil | None, estado: str | None, busqueda: str | None
    ) -> list[Usuario]:
        """Delega el listado filtrado en el caso de uso correspondiente."""
        return await self._listar_cuentas.execute(rol, estado, busqueda)

    async def obtener_cuenta(self, usuario_id: UUID) -> Usuario:
        """Delega el detalle de una cuenta puntual en el caso de uso correspondiente."""
        return await self._obtener_cuenta.execute(usuario_id)
