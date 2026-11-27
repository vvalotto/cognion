"""`US-12.2.4` (`ADR-031`): cada tipo de salida de un presenter tiene los campos de su esquema de la API.

FastAPI valida el `dataclass` contra el `response_model`; si los campos difieren, la respuesta cambia en silencio
(un campo que falta se rechaza y uno que sobra se descarta). Esta prueba los compara por nombre.
"""

from __future__ import annotations

import dataclasses
import importlib
import inspect

import pytest
from pydantic import BaseModel

BCS = ["analytics", "banco_preguntas", "identidad", "actividad_evaluativa"]


def _salidas(bc: str) -> list[tuple[str, type]]:
    from pathlib import Path

    carpeta = Path(__file__).resolve().parents[3] / "src" / bc / "interface_adapters" / "presenters"
    pares: list[tuple[str, type]] = []
    for archivo in sorted(carpeta.glob("*.py")) if carpeta.exists() else []:
        modulo = importlib.import_module(f"src.{bc}.interface_adapters.presenters.{archivo.stem}")
        for nombre, clase in inspect.getmembers(modulo, inspect.isclass):
            if (
                dataclasses.is_dataclass(clase)
                and nombre.endswith("Salida")
                and clase.__module__ == modulo.__name__
            ):
                pares.append((nombre, clase))
    return pares


CASOS = [(bc, nombre, clase) for bc in BCS for nombre, clase in _salidas(bc)]


@pytest.mark.parametrize(("bc", "nombre", "clase"), CASOS, ids=[f"{c[0]}.{c[1]}" for c in CASOS])
def test_la_salida_tiene_los_campos_del_esquema(bc: str, nombre: str, clase: type) -> None:
    esquemas = importlib.import_module(f"src.{bc}.frameworks.api.schemas")
    esquema = getattr(esquemas, nombre[: -len("Salida")] + "Response", None)
    if esquema is None:
        pytest.skip("sin esquema homónimo: la salida no es un modelo de respuesta directo")
    assert issubclass(esquema, BaseModel)
    assert [f.name for f in dataclasses.fields(clase)] == list(esquema.model_fields)
