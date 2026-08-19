"""Caso de uso: autenticación de un Usuario y emisión de su JWT."""

from __future__ import annotations

from src.identidad.entities.errors import CredencialesInvalidas, CuentaBloqueadaError
from src.identidad.entities.eventos import CuentaBloqueada, SesionIniciada
from src.identidad.entities.ports.password_hasher_port import PasswordHasherPort
from src.identidad.entities.ports.usuario_repository_port import UsuarioRepositoryPort
from src.shared.entities.jwt import JWT
from src.shared.entities.ports.jwt_issuer_port import JWTIssuerPort

_INTENTOS_MAXIMOS = 3


class IniciarSesionUseCase:
    """Verifica credenciales y emite un JWT con el rol del `Usuario` autenticado (RF-02).

    Lleva el contador de intentos fallidos de login y bloquea la cuenta al 3er fallo
    consecutivo (RF-19, INV-ID-10, `US-2.2.1`).
    """

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
        una cuenta existe (`US-1.1.4`). Lanza `CuentaBloqueadaError` sin verificar la
        contraseña si la cuenta ya está bloqueada (no consume intentos adicionales).
        """
        usuario = await self._usuario_repositorio.obtener_por_email(email)
        if usuario is None:
            raise CredencialesInvalidas

        if usuario.bloqueada:
            raise CuentaBloqueadaError(usuario.id)

        if not self._hasher.verificar(password, usuario.password_hash):
            usuario.intentos_fallidos_login += 1
            exc = CredencialesInvalidas()
            if usuario.intentos_fallidos_login >= _INTENTOS_MAXIMOS:
                usuario.bloqueada = True
                exc.evento_cuenta_bloqueada = CuentaBloqueada(usuario_id=usuario.id)
            await self._usuario_repositorio.actualizar(usuario)
            raise exc

        usuario.intentos_fallidos_login = 0
        await self._usuario_repositorio.actualizar(usuario)

        jwt = self._jwt_issuer.emitir(usuario.id, usuario.tipo_perfil)
        evento = SesionIniciada(usuario_id=usuario.id, rol=usuario.tipo_perfil)
        return jwt, evento
