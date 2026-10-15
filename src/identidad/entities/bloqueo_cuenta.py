"""Política de bloqueo de cuentas por intentos fallidos (INV-ID-10, INV-ID-20, INV-ID-21).

Funciones de dominio puras sobre `Usuario`, fuera de la entidad para que esta no crezca con cada
regla de ciclo de vida de la cuenta.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from src.identidad.entities.usuario import Administrador, Usuario


def es_administrador_operativo(usuario: Usuario) -> bool:
    """Indica si es un Administrador que puede operar: ni deshabilitado ni bloqueado."""
    return (
        isinstance(usuario.perfil, Administrador)
        and not usuario.deshabilitada
        and not usuario.bloqueada
    )


def bloquear_por_intentos_fallidos(
    usuario: Usuario, es_ultimo_administrador: bool, ahora: datetime, duracion: timedelta
) -> None:
    """Bloquea la cuenta tras el 3er fallo consecutivo (INV-ID-10, INV-ID-21).

    El último Administrador operativo queda bloqueado solo hasta `ahora + duracion`, para que el
    sistema no quede sin quien lo opere; cualquier otra cuenta, de forma permanente.
    """
    usuario.bloqueada = True
    usuario.bloqueada_hasta = ahora + duracion if es_ultimo_administrador else None


def tiene_bloqueo_temporal_vigente(usuario: Usuario, ahora: datetime) -> bool:
    """Indica si está bloqueada con un bloqueo temporal que todavía no venció."""
    return (
        usuario.bloqueada
        and usuario.bloqueada_hasta is not None
        and ahora < usuario.bloqueada_hasta
    )


def levantar_bloqueo_si_vencio(usuario: Usuario, ahora: datetime) -> bool:
    """Levanta un bloqueo temporal ya vencido, reseteando los contadores (vencimiento perezoso).

    Devuelve `True` si levantó el bloqueo. No toca un bloqueo permanente ni uno vigente.
    """
    hasta = usuario.bloqueada_hasta
    if not usuario.bloqueada or hasta is None or ahora < hasta:
        return False
    usuario.bloqueada = False
    usuario.bloqueada_hasta = None
    usuario.intentos_fallidos_login = 0
    usuario.intentos_fallidos_password = 0
    return True
