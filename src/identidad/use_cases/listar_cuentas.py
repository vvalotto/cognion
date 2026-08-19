"""Caso de uso: listado de cuentas de usuario filtrable por rol, estado y búsqueda."""

from __future__ import annotations

from src.identidad.entities.ports.cuenta_query_port import CuentaQueryPort
from src.identidad.entities.usuario import Usuario
from src.shared.entities.tipo_perfil import TipoPerfil


class ListarCuentasUseCase:
    """Consulta de solo lectura sobre `Usuario`, sin invariantes de dominio (RF-03)."""

    def __init__(self, cuenta_query: CuentaQueryPort) -> None:
        """Recibe el puerto de consulta de cuentas a usar."""
        self._cuenta_query = cuenta_query

    async def execute(
        self, rol: TipoPerfil | None, estado: str | None, busqueda: str | None
    ) -> list[Usuario]:
        """Delega el filtrado combinado (AND) en el puerto de consulta."""
        return await self._cuenta_query.listar(rol, estado, busqueda)
