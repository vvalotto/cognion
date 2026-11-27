"""`US-12.2.2` y `US-12.2.4`: el esquema OpenAPI de la API no cambia con estas refactorizaciones.

La instantánea (`golden/openapi.json`) se generó antes del primer cambio de `US-12.2.2` (66 rutas y
91 esquemas). Si una historia cambia la API a propósito, se regenera y el cambio se explica en su
reporte; si cambia sin querer, este test lo atrapa.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.app import app

INSTANTANEA = Path(__file__).parent / "golden" / "openapi.json"


def _normalizado(esquema: dict) -> str:
    return json.dumps(esquema, sort_keys=True, ensure_ascii=False, indent=1)


def test_el_esquema_openapi_es_identico_a_la_instantanea() -> None:
    esperado = json.loads(INSTANTANEA.read_text(encoding="utf-8"))
    assert _normalizado(app.openapi()) == _normalizado(esperado)


def test_la_instantanea_tiene_las_cifras_medidas() -> None:
    esperado = json.loads(INSTANTANEA.read_text(encoding="utf-8"))
    assert len(esperado["paths"]) == 66
    assert len(esperado["components"]["schemas"]) == 91
