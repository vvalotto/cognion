"""Caso de uso: listado de cuentas de usuario filtrable por rol, estado y búsqueda."""

from __future__ import annotations

from src.identidad.entities.ports.cuenta_query_port import CuentaQueryPort
from src.identidad.entities.resultado_paginado_cuentas import ResultadoPaginadoCuentas
from src.shared.entities.tipo_perfil import TipoPerfil


class ListarCuentasUseCase:
    """Consulta de solo lectura sobre `Usuario`, sin invariantes de dominio (RF-03)."""

    def __init__(self, cuenta_query: CuentaQueryPort) -> None:
        """Recibe el puerto de consulta de cuentas a usar."""
        self._cuenta_query = cuenta_query

    async def execute(
        self,
        rol: TipoPerfil | None,
        estado: str | None,
        busqueda: str | None,
        pagina: int = 1,
        tamanio_pagina: int = 20,
    ) -> ResultadoPaginadoCuentas:
        """Delega el filtrado combinado (AND) y la paginación en el puerto de consulta."""
        return await self._cuenta_query.listar(rol, estado, busqueda, pagina, tamanio_pagina)
