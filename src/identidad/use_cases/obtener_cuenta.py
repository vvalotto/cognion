"""Caso de uso: detalle de una cuenta de usuario puntual."""

from __future__ import annotations

from uuid import UUID

from src.identidad.entities.errors import UsuarioNoExiste
from src.identidad.entities.ports.usuario_repository_port import UsuarioRepositoryPort
from src.identidad.entities.usuario import Usuario


class ObtenerCuentaUseCase:
    """Consulta de solo lectura sobre un `Usuario` puntual, sin invariantes de dominio (RF-03)."""

    def __init__(self, usuario_repositorio: UsuarioRepositoryPort) -> None:
        """Recibe el repositorio de usuarios a usar."""
        self._usuario_repositorio = usuario_repositorio

    async def execute(self, usuario_id: UUID) -> Usuario:
        """Devuelve el `Usuario` completo; lanza `UsuarioNoExiste` si no está registrado."""
        usuario = await self._usuario_repositorio.obtener_por_id(usuario_id)
        if usuario is None:
            raise UsuarioNoExiste(usuario_id)
        return usuario
