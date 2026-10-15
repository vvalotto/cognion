"""Caso de uso: autenticación de un Usuario y emisión de su JWT."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from src.identidad.entities.bloqueo_cuenta import bloquear_por_intentos_fallidos
from src.identidad.entities.errors import (
    CredencialesInvalidas,
    CuentaDeshabilitadaError,
)
from src.identidad.entities.eventos import CuentaBloqueada, SesionIniciada
from src.identidad.entities.ports.password_hasher_port import PasswordHasherPort
from src.identidad.entities.ports.usuario_repository_port import UsuarioRepositoryPort
from src.identidad.use_cases.politica_bloqueo import (
    es_ultimo_administrador_operativo,
    rechazar_si_bloqueada,
)
from src.shared.entities.jwt import JWT
from src.shared.entities.ports.jwt_issuer_port import JWTIssuerPort

_INTENTOS_MAXIMOS = 3
_BLOQUEO_TEMPORAL_POR_DEFECTO = timedelta(minutes=15)


class IniciarSesionUseCase:
    """Verifica credenciales y emite un JWT con el rol del `Usuario` autenticado (RF-02).

    Lleva el contador de intentos fallidos de login y bloquea la cuenta al 3er fallo
    consecutivo (RF-19, INV-ID-10, `US-2.2.1`). Rechaza antes que nada las cuentas dadas de baja
    (`deshabilitada`, INV-ID-18, `US-ADJ-59`).
    """

    def __init__(
        self,
        usuario_repositorio: UsuarioRepositoryPort,
        hasher: PasswordHasherPort,
        jwt_issuer: JWTIssuerPort,
        duracion_bloqueo_temporal: timedelta = _BLOQUEO_TEMPORAL_POR_DEFECTO,
    ) -> None:
        """Recibe el repositorio, el hasher, el emisor de JWT y la duración del bloqueo temporal."""
        self._duracion_bloqueo_temporal = duracion_bloqueo_temporal
        self._usuario_repositorio = usuario_repositorio
        self._hasher = hasher
        self._jwt_issuer = jwt_issuer

    async def execute(self, email: str, password: str) -> tuple[JWT, SesionIniciada]:
        """Autentica por email y contraseña y emite el JWT correspondiente.

        Lanza `CredencialesInvalidas` tanto si el email no existe como si la contraseña no
        verifica contra el hash guardado — el mismo error en ambos casos, para no filtrar si
        una cuenta existe (`US-1.1.4`). Lanza `CuentaDeshabilitadaError` sin verificar la
        contraseña ni tocar los contadores si la cuenta está dada de baja (INV-ID-18) — tiene
        prioridad sobre el bloqueo porque es la decisión manual del Administrador. Lanza
        `CuentaBloqueadaError` sin verificar la contraseña si la cuenta ya está bloqueada (no
        consume intentos adicionales).
        """
        usuario = await self._usuario_repositorio.obtener_por_email(email)
        if usuario is None:
            raise CredencialesInvalidas

        if usuario.deshabilitada:
            raise CuentaDeshabilitadaError(usuario.id)

        ahora = datetime.now(UTC)
        await rechazar_si_bloqueada(self._usuario_repositorio, usuario, ahora)

        if not self._hasher.verificar(password, usuario.password_hash):
            usuario.intentos_fallidos_login += 1
            exc = CredencialesInvalidas()
            if usuario.intentos_fallidos_login >= _INTENTOS_MAXIMOS:
                es_ultimo = await es_ultimo_administrador_operativo(
                    self._usuario_repositorio, usuario
                )
                bloquear_por_intentos_fallidos(
                    usuario, es_ultimo, ahora, self._duracion_bloqueo_temporal
                )
                exc.evento_cuenta_bloqueada = CuentaBloqueada(usuario_id=usuario.id)
            await self._usuario_repositorio.actualizar(usuario)
            raise exc

        usuario.intentos_fallidos_login = 0
        await self._usuario_repositorio.actualizar(usuario)

        jwt = self._jwt_issuer.emitir(usuario.id, usuario.tipo_perfil, usuario.nombre)
        evento = SesionIniciada(usuario_id=usuario.id, rol=usuario.tipo_perfil)
        return jwt, evento
