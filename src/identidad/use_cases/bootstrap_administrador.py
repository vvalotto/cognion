"""Caso de uso: alta del primer Administrador de una instalación limpia (`ADR-016`, `US-8.1.5`)."""

from __future__ import annotations

from src.identidad.entities.errors import AdministradorYaExiste
from src.identidad.entities.ports.password_hasher_port import PasswordHasherPort
from src.identidad.entities.ports.usuario_repository_port import UsuarioRepositoryPort
from src.identidad.entities.usuario import Usuario
from src.identidad.use_cases.crear_usuario import CrearUsuarioUseCase
from src.shared.entities.tipo_perfil import TipoPerfil


class BootstrapAdministradorUseCase:
    """Crea el primer Administrador, y no hace nada si ya existe uno operativo."""

    def __init__(self, repositorio: UsuarioRepositoryPort, hasher: PasswordHasherPort) -> None:
        """Recibe el repositorio de usuarios y el hasher que usa el alta."""
        self._repositorio = repositorio
        self._crear_usuario = CrearUsuarioUseCase(repositorio, hasher)

    async def execute(self, nombre: str, email: str, password: str) -> Usuario:
        """Crea y devuelve el Administrador.

        Lanza `AdministradorYaExiste` si ya hay un Administrador operativo, y las mismas
        excepciones que `CrearUsuarioUseCase` si el email está en uso o la contraseña no
        cumple INV-ID-11.
        """
        if await self._repositorio.contar_administradores_operativos() > 0:
            raise AdministradorYaExiste()
        usuario, _evento = await self._crear_usuario.execute(
            nombre, email, password, TipoPerfil.ADMINISTRADOR
        )
        return usuario
