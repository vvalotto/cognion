"""Piezas compartidas de la política de bloqueo de cuentas (INV-ID-10, INV-ID-21)."""

from __future__ import annotations

from datetime import datetime

from src.identidad.entities.errors import CuentaBloqueadaError, CuentaBloqueadaTemporalmenteError
from src.identidad.entities.ports.usuario_repository_port import UsuarioRepositoryPort
from src.identidad.entities.usuario import Usuario


async def es_ultimo_administrador_operativo(
    usuario_repositorio: UsuarioRepositoryPort, usuario: Usuario
) -> bool:
    """Indica si `usuario` es un Administrador operativo y no existe otro (INV-ID-20/21)."""
    if not usuario.es_administrador_operativo():
        return False
    otros = await usuario_repositorio.contar_administradores_operativos(excluyendo=usuario.id)
    return otros == 0


async def rechazar_si_bloqueada(
    usuario_repositorio: UsuarioRepositoryPort, usuario: Usuario, ahora: datetime
) -> None:
    """Rechaza el acceso de una cuenta bloqueada, levantando antes un bloqueo temporal vencido.

    Lanza `CuentaBloqueadaTemporalmenteError` si el bloqueo temporal rige y `CuentaBloqueadaError`
    si es permanente (INV-ID-10, INV-ID-21). El vencimiento es perezoso: se evalúa acá, sin
    proceso de fondo.
    """
    if usuario.levantar_bloqueo_si_vencio(ahora):
        await usuario_repositorio.actualizar(usuario)
    if usuario.bloqueada_hasta is not None and usuario.tiene_bloqueo_temporal_vigente(ahora):
        raise CuentaBloqueadaTemporalmenteError(usuario.id, usuario.bloqueada_hasta)
    if usuario.bloqueada:
        raise CuentaBloqueadaError(usuario.id)
