"""`US-12.2.6` (`IQ-01`): el umbral de CBO se mide, no se esquiva, y no sube sin que se note.

`CBOAnalyzer` cuenta las clases distintas que una clase referencia. Cuando el umbral aprieta, la salida
tentadora es esconder acoplamiento (funciones sueltas, tipos `object`) en vez de bajarlo. El valor vigente
está declarado acá: subirlo en `pyproject.toml` sin actualizarlo falla, y obliga a explicar por qué.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]

# Valor medido tras revertir los atajos de `US-12.2.6` (reporte `docs/reports/inc12/US-12.2.6-report.md`).
MAX_CBO_DECLARADO = 12


def _max_cbo() -> int:
    config = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))
    return int(config["tool"]["designreviewer"]["max_cbo"])


def test_el_umbral_de_cbo_es_el_declarado() -> None:
    assert _max_cbo() == MAX_CBO_DECLARADO, (
        f"max_cbo es {_max_cbo()} y el test declara {MAX_CBO_DECLARADO}: si lo cambiaste a propósito, "
        "actualizá MAX_CBO_DECLARADO y explicá la medición en el reporte (US-12.2.6)"
    )


def test_el_codigo_no_declara_atajos_para_esquivar_el_cbo() -> None:
    """Ningún `src/` vuelve a tipar `object` ni a mover código «para no sumar CBO»."""
    frases = (
        "para no sumar cbo",
        "para no acumular cbo",
        "fuera de la clase por cbo",
        "se tipa como `object`",
    )
    ofensores = []
    for archivo in (RAIZ / "src").rglob("*.py"):
        texto = archivo.read_text(encoding="utf-8").lower()
        ofensores += [f"{archivo.relative_to(RAIZ)}: {f}" for f in frases if f in texto]

    assert ofensores == []
