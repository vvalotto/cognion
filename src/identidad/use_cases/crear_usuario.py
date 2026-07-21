from __future__ import annotations

from src.identidad.entities.errors import EmailYaRegistrado
from src.identidad.entities.eventos import UsuarioCreado
from src.identidad.entities.ports.password_hasher_port import PasswordHasherPort
from src.identidad.entities.ports.usuario_repository_port import UsuarioRepositoryPort
from src.identidad.entities.usuario import TipoPerfil, Usuario


class CrearUsuarioUseCase:
    def __init__(self, repositorio: UsuarioRepositoryPort, hasher: PasswordHasherPort) -> None:
        self._repositorio = repositorio
        self._hasher = hasher

    async def execute(
        self, nombre: str, email: str, password: str, tipo_perfil: TipoPerfil
    ) -> tuple[Usuario, UsuarioCreado]:
        if await self._repositorio.existe_email(email):
            raise EmailYaRegistrado(email)

        password_hash = self._hasher.hash(password)
        usuario = Usuario.crear(nombre, email, password_hash, tipo_perfil)
        await self._repositorio.guardar(usuario)

        evento = UsuarioCreado(
            usuario_id=usuario.id, email=usuario.email, tipo_perfil=usuario.tipo_perfil.value
        )
        return usuario, evento
