"""Los contratos de `import-linter` detectan una violación sembrada de cada tipo (Issue #497).

La guarda de arquitectura no vale nada si no falla cuando debe: cada prueba siembra un import prohibido en
un módulo temporal de `src/`, corre `lint-imports` y exige que el contrato correspondiente se rompa. El
módulo se borra siempre, aun si la prueba falla.
"""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[3]
LINT_IMPORTS = Path(sys.executable).parent / "lint-imports"
MODULO_SEMBRADO = "_violacion_sembrada.py"


def _correr() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(LINT_IMPORTS)], cwd=RAIZ, capture_output=True, text=True, check=False
    )


@contextmanager
def _sembrar(ruta_relativa: str, codigo: str) -> Iterator[None]:
    """Crea un módulo con un import prohibido y lo borra al salir."""
    ruta = RAIZ / ruta_relativa
    ruta.write_text(codigo, encoding="utf-8")
    try:
        yield
    finally:
        ruta.unlink(missing_ok=True)


def test_el_estado_actual_cumple_todos_los_contratos():
    resultado = _correr()

    assert resultado.returncode == 0, resultado.stdout[-1500:]
    assert ", 0 broken" in resultado.stdout


@pytest.mark.parametrize(
    ("modulo", "import_prohibido", "contrato"),
    [
        (
            f"src/identidad/entities/{MODULO_SEMBRADO}",
            "from src.identidad.use_cases import obtener_invitacion\n",
            "Capas dentro de cada BC",
        ),
        (
            f"src/identidad/use_cases/{MODULO_SEMBRADO}",
            "from src.banco_preguntas.entities import materia\n",
            "Aislamiento entre BC",
        ),
        (
            f"src/shared/entities/{MODULO_SEMBRADO}",
            "from src.identidad.entities import usuario\n",
            "shared no importa de ningún BC",
        ),
        (
            f"src/notificaciones/frameworks/adapters/{MODULO_SEMBRADO}",
            "from src.identidad.frameworks.db import models\n",
            "ADR-026",
        ),
    ],
    ids=["capas", "aislamiento-entre-bc", "shared", "adr-026-modelos-orm"],
)
def test_una_violacion_sembrada_rompe_su_contrato(modulo, import_prohibido, contrato):
    with _sembrar(modulo, import_prohibido):
        resultado = _correr()

    assert resultado.returncode != 0
    rotos = resultado.stdout.split("Broken contracts")[-1]
    assert contrato in rotos
    assert not (RAIZ / modulo).exists()
