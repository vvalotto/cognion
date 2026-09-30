"""Caso de uso: autoregistro de un Docente sin invitación ni Administrador."""

from __future__ import annotations

from src.identidad.entities.errors import EmailYaRegistrado
from src.identidad.entities.eventos import UsuarioAutoregistrado
from src.identidad.entities.ports.password_hasher_port import PasswordHasherPort
from src.identidad.entities.ports.usuario_repository_port import UsuarioRepositoryPort
from src.identidad.entities.usuario import Usuario
from src.shared.entities.tipo_perfil import TipoPerfil


class AutoregistrarDocenteUseCase:
    """Crea una cuenta de Docente activa de inmediato (INV-ID-16), sin actor autenticado."""

    def __init__(self, repositorio: UsuarioRepositoryPort, hasher: PasswordHasherPort) -> None:
        """Recibe el repositorio de usuarios y el hasher de contraseñas a usar."""
        self._repositorio = repositorio
        self._hasher = hasher

    async def execute(
        self, nombre: str, email: str, password: str
    ) -> tuple[Usuario, UsuarioAutoregistrado]:
        """Crea y persiste el Docente, y devuelve el usuario junto al evento emitido.

        Lanza `EmailYaRegistrado` si el email ya está en uso, o `PasswordDemasiadoCorta`/
        `PasswordSinComplejidadSuficiente` si `password` no cumple INV-ID-11 (ampliada).
        """
        if await self._repositorio.existe_email(email):
            raise EmailYaRegistrado(email)

        Usuario.validar_password_nueva(password)
        password_hash = self._hasher.hash(password)
        usuario = Usuario.crear(nombre, email, password_hash, TipoPerfil.DOCENTE)
        await self._repositorio.guardar(usuario)

        evento = UsuarioAutoregistrado(
            usuario_id=usuario.id, email=usuario.email, tipo_perfil=usuario.tipo_perfil.value
        )
        return usuario, evento
