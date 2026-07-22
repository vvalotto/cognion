"""Controller de la API para operaciones sobre usuarios."""

from __future__ import annotations

from src.identidad.entities.eventos import UsuarioCreado
from src.identidad.entities.usuario import TipoPerfil, Usuario
from src.identidad.use_cases.crear_usuario import CrearUsuarioUseCase


class UsuariosController:
    """Adapta requests HTTP a los casos de uso de usuarios."""

    def __init__(self, crear_usuario: CrearUsuarioUseCase) -> None:
        """Recibe el caso de uso de creación de usuario a usar."""
        self._crear_usuario = crear_usuario

    async def crear_usuario(
        self, nombre: str, email: str, password: str, tipo_perfil: TipoPerfil
    ) -> tuple[Usuario, UsuarioCreado]:
        """Delega la creación del usuario en el caso de uso correspondiente."""
        return await self._crear_usuario.execute(nombre, email, password, tipo_perfil)
