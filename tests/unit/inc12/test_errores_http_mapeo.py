"""`US-12.2.2` (`ADR-029`): cada error de dominio recibe su categoría y el manejador lo traduce a HTTP.

La tabla dorada (`golden/errores_http.json`) se generó **antes** de tocar nada, a partir de las
traducciones que hacían a mano los 19 routers (136 `raise HTTPException`): para cada una de las 78
clases, el código HTTP que recibía. Las 8 que ningún router traducía se decidieron en la Fase 0.
"""

from __future__ import annotations

import importlib
import inspect
import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.shared.entities.errors import (
    Conflicto,
    ErrorDeDominio,
    NoAutenticado,
    NoAutorizado,
    NoEncontrado,
    ReglaViolada,
)
from src.shared.frameworks.api.errores import registrar_manejador, status_de

TABLA = json.loads((Path(__file__).parent / "golden" / "errores_http.json").read_text("utf-8"))
CATEGORIAS = {
    "NoEncontrado": NoEncontrado,
    "NoAutorizado": NoAutorizado,
    "NoAutenticado": NoAutenticado,
    "ReglaViolada": ReglaViolada,
    "Conflicto": Conflicto,
}
RAIZ = Path(__file__).resolve().parents[3]


def _clase(clave: str) -> type[Exception]:
    contexto, nombre = clave.split(".")
    return getattr(importlib.import_module(f"src.{contexto}.entities.errors"), nombre)


def test_la_tabla_dorada_tiene_las_78_clases() -> None:
    assert len(TABLA) == 78


@pytest.mark.parametrize("clave", sorted(TABLA))
def test_cada_clase_recibe_el_codigo_http_de_la_tabla(clave: str) -> None:
    clase = _clase(clave)
    esperado = TABLA[clave]
    assert issubclass(clase, CATEGORIAS[esperado["categoria"]]), clave
    assert status_de(clase) == esperado["status"], clave


def test_toda_clase_de_un_errors_py_hereda_de_error_de_dominio() -> None:
    """Un error nuevo no puede quedar sin categoría (saldría como 500)."""
    sin_categoria: list[str] = []
    for archivo in sorted(RAIZ.glob("src/*/entities/errors.py")):
        modulo = importlib.import_module(archivo.relative_to(RAIZ).with_suffix("").as_posix().replace("/", "."))
        for nombre, clase in inspect.getmembers(modulo, inspect.isclass):
            if clase.__module__ == modulo.__name__ and not issubclass(clase, ErrorDeDominio):
                sin_categoria.append(f"{modulo.__name__}.{nombre}")
    assert sin_categoria == []


@pytest.mark.parametrize(
    ("categoria", "codigo"),
    [
        (NoEncontrado, 404),
        (NoAutorizado, 403),
        (NoAutenticado, 401),
        (ReglaViolada, 422),
        (Conflicto, 409),
    ],
)
def test_el_manejador_traduce_la_categoria_con_el_detail_de_siempre(
    categoria: type[ErrorDeDominio], codigo: int
) -> None:
    app = FastAPI()
    registrar_manejador(app)

    @app.get("/falla")
    async def falla() -> None:
        raise categoria("mensaje de prueba")

    respuesta = TestClient(app).get("/falla")
    assert respuesta.status_code == codigo
    assert respuesta.json() == {"detail": "mensaje de prueba"}


def test_un_error_con_codigo_responde_el_objeto_estructurado() -> None:
    class ConCodigo(ReglaViolada):
        codigo = "algo_paso"

    app = FastAPI()
    registrar_manejador(app)

    @app.get("/falla")
    async def falla() -> None:
        raise ConCodigo("texto")

    respuesta = TestClient(app).get("/falla")
    assert respuesta.status_code == 422
    assert respuesta.json() == {"detail": {"codigo": "algo_paso", "mensaje": "texto"}}
