"""Controller de la API para la administración de cuentas de usuario (RF-03)."""

from __future__ import annotations

from src.identidad.entities.usuario import Usuario
from src.identidad.use_cases.listar_cuentas import ListarCuentasUseCase
from src.shared.entities.tipo_perfil import TipoPerfil


class CuentasController:
    """Adapta requests HTTP a los casos de uso de administración de cuentas."""

    def __init__(self, listar_cuentas: ListarCuentasUseCase) -> None:
        """Recibe el caso de uso de listado de cuentas a usar."""
        self._listar_cuentas = listar_cuentas

    async def listar_cuentas(
        self, rol: TipoPerfil | None, estado: str | None, busqueda: str | None
    ) -> list[Usuario]:
        """Delega el listado filtrado en el caso de uso correspondiente."""
        return await self._listar_cuentas.execute(rol, estado, busqueda)
