"""Caso de uso: reactivar una cuenta previamente deshabilitada."""

from __future__ import annotations

from uuid import UUID

from src.identidad.entities.errors import UsuarioNoExiste
from src.identidad.entities.ports.usuario_repository_port import UsuarioRepositoryPort
from src.identidad.entities.usuario import Usuario


class ActivarCuentaUseCase:
    """Reactiva una cuenta deshabilitada, volviéndola a mostrar en los listados normales."""

    def __init__(self, usuario_repositorio: UsuarioRepositoryPort) -> None:
        """Recibe el repositorio de usuarios a usar."""
        self._usuario_repositorio = usuario_repositorio

    async def execute(self, usuario_id: UUID) -> Usuario:
        """Activa `usuario_id`. Lanza `UsuarioNoExiste` si no existe."""
        usuario = await self._usuario_repositorio.obtener_por_id(usuario_id)
        if usuario is None:
            raise UsuarioNoExiste(usuario_id)

        usuario.activar()
        await self._usuario_repositorio.actualizar(usuario)
        return usuario
