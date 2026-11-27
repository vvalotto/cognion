"""Traducción de los errores de dominio a respuestas HTTP, en un solo lugar (`ADR-029`).

Cada categoría de `shared/entities/errors.py` tiene su código HTTP. Un router no traduce a mano un
error de dominio: lo deja subir y el manejador registrado en `app.py` responde con el código de su
categoría y el `detail` que arma el propio error (`detalle()`). Un router conserva un `except`
propio solo cuando la respuesta depende del endpoint y no del error.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.shared.entities.errors import (
    Conflicto,
    ErrorDeDominio,
    NoAutenticado,
    NoAutorizado,
    NoEncontrado,
    ReglaViolada,
)

STATUS_POR_CATEGORIA: dict[type[ErrorDeDominio], int] = {
    NoEncontrado: 404,
    NoAutorizado: 403,
    NoAutenticado: 401,
    ReglaViolada: 422,
    Conflicto: 409,
}


def status_de(clase: type[BaseException]) -> int | None:
    """Código HTTP de una clase de error según su categoría; `None` si no tiene categoría."""
    for categoria, codigo in STATUS_POR_CATEGORIA.items():
        if issubclass(clase, categoria):
            return codigo
    return None


async def _responder(_: Request, exc: Exception) -> JSONResponse:
    """Arma la respuesta de un error de dominio con el código de su categoría."""
    if not isinstance(exc, ErrorDeDominio):  # pragma: no cover - FastAPI solo nos pasa estos
        raise exc
    codigo = status_de(type(exc))
    if codigo is None:
        raise exc
    return JSONResponse(status_code=codigo, content={"detail": exc.detalle()})


def registrar_manejador(app: FastAPI) -> None:
    """Registra el manejador único de los errores de dominio en la aplicación."""
    app.add_exception_handler(ErrorDeDominio, _responder)
