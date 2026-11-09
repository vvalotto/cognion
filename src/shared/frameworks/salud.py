"""Chequeo de readiness de la aplicación: ¿puede atender pedidos? (`US-8.3.3`).

`GET /health` solo dice que el proceso está vivo. `GET /health/ready` comprueba además que la base
de datos responde, para distinguir "el proceso está en pie" de "no puede atender pedidos".
"""

from __future__ import annotations

import asyncio
import logging
import re

from sqlalchemy import text
from sqlalchemy.engine import make_url

from src.settings import settings
from src.shared.frameworks.db import SessionLocal

logger = logging.getLogger(__name__)

TIEMPO_MAXIMO_SEGUNDOS = 2.0

# `esquema://usuario:clave@host`: el usuario y la clave de cualquier URL de conexión.
_CREDENCIALES_EN_URL = re.compile(r"([A-Za-z][A-Za-z0-9+.-]*://)[^/\s:@]+:[^/\s@]*@")


def sin_credenciales(texto: str) -> str:
    """Quita del texto el `usuario:clave@` de las URLs y la contraseña configurada de la base.

    Un error de conexión puede traer la URL completa; ni el log ni la respuesta llevan la clave.
    """
    texto = _CREDENCIALES_EN_URL.sub(r"\1***@", texto)
    clave = make_url(settings.database_url).password
    return texto.replace(clave, "***") if clave else texto


async def _consultar() -> None:
    """Ejecuta `SELECT 1` en una sesión nueva."""
    async with SessionLocal() as session:
        await session.execute(text("SELECT 1"))


async def base_disponible(tiempo_maximo: float = TIEMPO_MAXIMO_SEGUNDOS) -> bool:
    """Indica si la base responde un `SELECT 1` dentro de `tiempo_maximo` segundos.

    Cualquier fallo (conexión rechazada, credenciales, tiempo agotado) devuelve `False` y deja el
    motivo en el log sin credenciales; nunca lo propaga ni lo expone.
    """
    try:
        await asyncio.wait_for(_consultar(), timeout=tiempo_maximo)
    except TimeoutError:
        logger.error("La base de datos no respondió en %s segundos.", tiempo_maximo)
        return False
    # Readiness: todo fallo del chequeo cuenta como "no disponible", no como un error del endpoint.
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.error(
            "La base de datos no está disponible: %s: %s",
            type(exc).__name__,
            sin_credenciales(str(exc)),
        )
        return False
    return True


async def comprobar_base() -> bool:
    """Dependencia del endpoint de readiness; los tests la reemplazan con `dependency_overrides`."""
    return await base_disponible()
