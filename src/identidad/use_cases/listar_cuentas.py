"""Caso de uso: listado de cuentas de usuario filtrable por rol, estado y búsqueda."""

from __future__ import annotations

from src.identidad.entities.ports.usuario_repository_port import UsuarioRepositoryPort
from src.identidad.entities.usuario import Usuario
from src.shared.entities.tipo_perfil import TipoPerfil


class ListarCuentasUseCase:
    """Consulta de solo lectura sobre `Usuario`, sin invariantes de dominio (RF-03)."""

    def __init__(self, usuario_repositorio: UsuarioRepositoryPort) -> None:
        """Recibe el repositorio de usuarios a usar."""
        self._usuario_repositorio = usuario_repositorio

    async def execute(
        self, rol: TipoPerfil | None, estado: str | None, busqueda: str | None
    ) -> list[Usuario]:
        """Delega el filtrado combinado (AND) en el repositorio."""
        return await self._usuario_repositorio.listar(rol, estado, busqueda)
