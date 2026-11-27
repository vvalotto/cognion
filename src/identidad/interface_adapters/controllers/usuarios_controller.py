"""Controller de la API para operaciones sobre usuarios."""

from __future__ import annotations

from src.identidad.interface_adapters.presenters.identidad_presenter import (
    UsuarioSalida,
    presentar_usuario,
)
from src.identidad.use_cases.crear_usuario import CrearUsuarioUseCase
from src.shared.entities.tipo_perfil import TipoPerfil


class UsuariosController:
    """Adapta requests HTTP a los casos de uso de usuarios."""

    def __init__(self, crear_usuario: CrearUsuarioUseCase) -> None:
        """Recibe el caso de uso de creación de usuario a usar."""
        self._crear_usuario = crear_usuario

    async def crear_usuario(
        self, nombre: str, email: str, password: str, tipo_perfil: TipoPerfil
    ) -> UsuarioSalida:
        """Delega la creación del usuario en el caso de uso correspondiente."""
        usuario, _evento = await self._crear_usuario.execute(nombre, email, password, tipo_perfil)
        return presentar_usuario(usuario)
