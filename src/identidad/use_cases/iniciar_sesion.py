"""Caso de uso: autenticación de un Usuario y emisión de su JWT."""

from __future__ import annotations

from src.identidad.entities.errors import CredencialesInvalidas
from src.identidad.entities.eventos import SesionIniciada
from src.identidad.entities.jwt import JWT
from src.identidad.entities.ports.jwt_issuer_port import JWTIssuerPort
from src.identidad.entities.ports.password_hasher_port import PasswordHasherPort
from src.identidad.entities.ports.usuario_repository_port import UsuarioRepositoryPort


class IniciarSesionUseCase:
    """Verifica credenciales y emite un JWT con el rol del `Usuario` autenticado (RF-02)."""

    def __init__(
        self,
        usuario_repositorio: UsuarioRepositoryPort,
        hasher: PasswordHasherPort,
        jwt_issuer: JWTIssuerPort,
    ) -> None:
        """Recibe el repositorio de usuarios, el hasher y el emisor de JWT a usar."""
        self._usuario_repositorio = usuario_repositorio
        self._hasher = hasher
        self._jwt_issuer = jwt_issuer

    async def execute(self, email: str, password: str) -> tuple[JWT, SesionIniciada]:
        """Autentica por email y contraseña y emite el JWT correspondiente.

        Lanza `CredencialesInvalidas` tanto si el email no existe como si la contraseña no
        verifica contra el hash guardado — el mismo error en ambos casos, para no filtrar si
        una cuenta existe (`US-1.1.4`).
        """
        usuario = await self._usuario_repositorio.obtener_por_email(email)
        if usuario is None or not self._hasher.verificar(password, usuario.password_hash):
            raise CredencialesInvalidas

        jwt = self._jwt_issuer.emitir(usuario.id, usuario.tipo_perfil)
        evento = SesionIniciada(usuario_id=usuario.id, rol=usuario.tipo_perfil)
        return jwt, evento
