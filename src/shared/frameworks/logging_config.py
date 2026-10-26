"""Configuración de logging de la aplicación y enmascarado de tokens (`US-ADJ-64`).

`uvicorn` configura solo sus propios loggers: los de la aplicación (`src.*`) quedan sin handler y
sus `INFO` se descartan, así que el modo consola de emails (`US-8.5.2`) no mostraba nada. Además,
el log de acceso de `uvicorn` escribe la URL completa de cada pedido, con el JWT del canal
WebSocket (`?token=<JWT>`), el token de la invitación y el de recuperación de contraseña.
"""

from __future__ import annotations

import logging
import re
import sys
from typing import Any

# `token=<valor>` en una query string (el JWT del WebSocket, la invitación de `/registro?token=`).
_TOKEN_EN_QUERY = re.compile(r"(token=)[^&\s\"']+", re.IGNORECASE)
# `/recuperar-password/<token>` en la ruta del SPA; no toca `/solicitar` ni `/confirmar` de la API.
_TOKEN_EN_RUTA = re.compile(
    r"(/recuperar-password/)(?!(?:solicitar|confirmar)\b)[A-Za-z0-9_\-]{20,}"
)

_LOGGERS_DE_UVICORN = ("uvicorn.access", "uvicorn.error")
_FORMATO = "%(levelname)s:     %(message)s"


def enmascarar_tokens(texto: str) -> str:
    """Reemplaza el valor de un token de acceso por `***` y deja el resto del texto igual."""
    return _TOKEN_EN_RUTA.sub(r"\1***", _TOKEN_EN_QUERY.sub(r"\1***", texto))


def _sanear(valor: Any) -> Any:
    """Enmascara un argumento de log si es texto; cualquier otro valor pasa sin cambios."""
    return enmascarar_tokens(valor) if isinstance(valor, str) else valor


class _HandlerCognion(logging.StreamHandler):  # type: ignore[type-arg]  # pylint: disable=too-few-public-methods
    """Handler propio: permite reconocer el que ya instaló `configurar_logging` (idempotencia)."""


class FiltroTokens(logging.Filter):  # pylint: disable=too-few-public-methods
    """Enmascara tokens en el mensaje y en los argumentos de cada registro; nunca descarta uno."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Sanea `msg` y `args` del registro y lo deja pasar."""
        record.msg = _sanear(record.msg)
        if isinstance(record.args, tuple):
            record.args = tuple(_sanear(arg) for arg in record.args)
        elif isinstance(record.args, dict):
            record.args = {clave: _sanear(valor) for clave, valor in record.args.items()}
        return True


def configurar_logging(nivel: str = "INFO") -> None:
    """Muestra los logs de la aplicación y enmascara los tokens de las URLs de acceso de `uvicorn`.

    Es idempotente: importar la aplicación más de una vez no agrega handlers ni filtros repetidos.
    El handler va solo en el logger `src` y conserva `propagate`, de modo que `caplog` y un logger
    raíz propio siguen funcionando.
    """
    logger = logging.getLogger("src")
    logger.setLevel(nivel)
    if not any(isinstance(h, _HandlerCognion) for h in logger.handlers):
        handler = _HandlerCognion(sys.stderr)
        handler.setFormatter(logging.Formatter(_FORMATO))
        logger.addHandler(handler)
    for nombre in _LOGGERS_DE_UVICORN:
        destino = logging.getLogger(nombre)
        if not any(isinstance(f, FiltroTokens) for f in destino.filters):
            destino.addFilter(FiltroTokens())
