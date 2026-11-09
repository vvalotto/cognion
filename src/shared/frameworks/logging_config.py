"""Configuración de logging de la aplicación y enmascarado de tokens (`US-ADJ-64`).

`uvicorn` configura solo sus propios loggers: los de la aplicación (`src.*`) quedan sin handler y
sus `INFO` se descartan, así que el modo consola de emails (`US-8.5.2`) no mostraba nada. Además,
el log de acceso de `uvicorn` escribe la URL completa de cada pedido, con el JWT del canal
WebSocket (`?token=<JWT>`), el token de la invitación (en la query de `/registro` y en la ruta de
`/identidad/invitaciones/<token>`, `US-ADJ-68`) y el de recuperación de contraseña.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from datetime import UTC, datetime
from typing import Any, Literal, TextIO

# `token=<valor>` en una query string (el JWT del WebSocket, la invitación de `/registro?token=`).
_TOKEN_EN_QUERY = re.compile(r"(token=)[^&\s\"']+", re.IGNORECASE)
# `/recuperar-password/<token>` en la ruta del SPA; no toca `/solicitar` ni `/confirmar` de la API.
_TOKEN_EN_RUTA = re.compile(
    r"(/recuperar-password/)(?!(?:solicitar|confirmar)\b)[A-Za-z0-9_\-]{20,}"
)

# `/invitaciones/<token>` en la ruta de la API (`GET /identidad/invitaciones/{token}`, `US-ADJ-68`).
# El token de una invitación sin usar es una credencial vigente; no toca `.../<id>/invitaciones`.
_TOKEN_EN_RUTA_INVITACION = re.compile(r"(/invitaciones/)[A-Za-z0-9_\-]{20,}")

_LOGGERS_DE_UVICORN = ("uvicorn.access", "uvicorn.error")
# `uvicorn.error` usa el handler del logger `uvicorn`; `uvicorn.access` tiene el suyo.
_LOGGERS_CON_HANDLER_DE_UVICORN = ("uvicorn", "uvicorn.access", "uvicorn.error")
_FORMATO = "%(levelname)s:     %(message)s"


def enmascarar_tokens(texto: str) -> str:
    """Reemplaza el valor de un token de acceso por `***` y deja el resto del texto igual."""
    texto = _TOKEN_EN_QUERY.sub(r"\1***", texto)
    texto = _TOKEN_EN_RUTA.sub(r"\1***", texto)
    return _TOKEN_EN_RUTA_INVITACION.sub(r"\1***", texto)


def _sanear(valor: Any) -> Any:
    """Enmascara un argumento de log si es texto; cualquier otro valor pasa sin cambios."""
    return enmascarar_tokens(valor) if isinstance(valor, str) else valor


class _HandlerCognion(logging.StreamHandler[TextIO]):  # pylint: disable=too-few-public-methods
    """Handler propio: permite reconocer el que ya instaló `configurar_logging` (idempotencia)."""


class FormateadorJson(logging.Formatter):
    """Escribe cada registro como un objeto JSON en una sola línea (`US-8.3.3`).

    Campos: `ts` (UTC, ISO 8601), `nivel`, `logger`, `mensaje` y, si el registro trae una excepción,
    `excepcion` con el traceback como texto. Vuelve a enmascarar el mensaje ya formateado y el
    traceback: `FiltroTokens` solo sanea `msg` y `args`, y un token puede llegar por otro camino.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Devuelve el registro como una línea JSON con los tokens enmascarados."""
        datos: dict[str, str] = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "nivel": record.levelname,
            "logger": record.name,
            "mensaje": enmascarar_tokens(record.getMessage()),
        }
        if record.exc_info:
            datos["excepcion"] = enmascarar_tokens(self.formatException(record.exc_info))
        return json.dumps(datos, ensure_ascii=False)


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


def _instalar_handler_de_src(formateador: logging.Formatter) -> None:
    """Deja un solo handler propio en el logger `src` y le asigna el formateador."""
    logger = logging.getLogger("src")
    handler = next((h for h in logger.handlers if isinstance(h, _HandlerCognion)), None)
    if handler is None:
        handler = _HandlerCognion(sys.stderr)
        logger.addHandler(handler)
    handler.setFormatter(formateador)


def _enmascarar_en_uvicorn() -> None:
    """Instala `FiltroTokens` en los loggers de acceso y error de `uvicorn`, una sola vez."""
    for nombre in _LOGGERS_DE_UVICORN:
        destino = logging.getLogger(nombre)
        if not any(isinstance(f, FiltroTokens) for f in destino.filters):
            destino.addFilter(FiltroTokens())


def _json_en_uvicorn() -> None:
    """Cambia a JSON el formato de los handlers que `uvicorn` ya instaló."""
    for nombre in _LOGGERS_CON_HANDLER_DE_UVICORN:
        for handler in logging.getLogger(nombre).handlers:
            handler.setFormatter(FormateadorJson())


def configurar_logging(nivel: str = "INFO", formato: Literal["texto", "json"] = "texto") -> None:
    """Muestra los logs de la aplicación y enmascara los tokens de las URLs de acceso de `uvicorn`.

    Con `formato="json"` los logs de la aplicación y los de `uvicorn` salen como un objeto JSON por
    línea (`FormateadorJson`); con `"texto"` (por defecto) quedan como siempre. Es idempotente:
    importar la aplicación más de una vez no agrega handlers ni filtros repetidos. El handler va
    solo en el logger `src` y conserva `propagate`, de modo que `caplog` y un logger raíz propio
    siguen funcionando.
    """
    logging.getLogger("src").setLevel(nivel)
    es_json = formato == "json"
    _instalar_handler_de_src(FormateadorJson() if es_json else logging.Formatter(_FORMATO))
    _enmascarar_en_uvicorn()
    if es_json:
        _json_en_uvicorn()
