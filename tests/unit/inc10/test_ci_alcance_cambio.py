"""Alcance del CI según los archivos del PR (`scripts/ci/alcance_cambio.sh`, `.github/workflows/ci.yml`).

Un PR que toca solo documentación que ningún test lee no necesita la suite completa; cualquier otra cosa, sí.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[3]
SCRIPT = RAIZ / "scripts" / "ci" / "alcance_cambio.sh"
CI = RAIZ / ".github" / "workflows" / "ci.yml"


def decidir(archivos: list[str]) -> str:
    """Corre el script con la lista de archivos y devuelve `true` o `false`."""
    salida = subprocess.run(
        [str(SCRIPT)],
        input="\n".join(archivos),
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return salida.removeprefix("completo=")


@pytest.mark.parametrize(
    "archivos",
    [
        ["docs/architecture/01-system-context.md"],
        ["docs/architecture/01.md", ".cm/baselines/BL-017.md"],
        ["quality/reports/designreviewer/x.json", "README.md", "CLAUDE.md"],
        ["docs/adr/ADR-028.md", "docs/design/domain/BC-x.md"],
    ],
)
def test_solo_documentacion_no_exige_ci_completo(archivos: list[str]) -> None:
    """Todo documentación segura: el CI pesado se saltea."""
    assert decidir(archivos) == "false"


@pytest.mark.parametrize(
    "archivos",
    [
        ["src/app.py"],
        ["docs/architecture/01.md", "src/app.py"],
        ["docs/INSTALACION.md"],  # la valida tests/unit/inc10 y viaja en el paquete
        ["CHANGELOG.md"],  # lo leen los tests de versión
        ["frontend/src/main.tsx"],
        [".github/workflows/ci.yml"],
        ["pyproject.toml"],
        ["scripts/ci/alcance_cambio.sh"],
        ["tests/unit/inc10/test_x.py"],
        ["docs/../src/app.py"],  # nunca se confía en un `..`
        ["otro/README.md"],  # un .md fuera de las rutas seguras no cuenta
        [],  # lista vacía: ante la duda, todo
    ],
)
def test_cualquier_otro_cambio_exige_ci_completo(archivos: list[str]) -> None:
    """Código, configuración, un archivo desconocido o una lista vacía: corre todo."""
    assert decidir(archivos) == "true"


def test_los_cuatro_checks_obligatorios_dependen_del_alcance_y_fallan_cerrados() -> None:
    """Los jobs de `develop` siguen existiendo; se saltean solo si `alcance` es explícito y, si falla, corren."""
    jobs = yaml.safe_load(CI.read_text(encoding="utf-8"))["jobs"]
    nombres = {j["name"] for j in jobs.values()}
    assert {"Lint backend", "Lint frontend", "Tests", "DesignReviewer"} <= nombres
    for clave in ("lint-backend", "lint-frontend", "test", "design-review"):
        assert jobs[clave]["needs"] == "alcance", clave
        condicion = jobs[clave]["if"]
        assert "always()" in condicion, clave
        assert "needs.alcance.result != 'success'" in condicion, clave
        assert "needs.alcance.outputs.completo == 'true'" in condicion, clave


def test_el_push_siempre_corre_completo() -> None:
    """Solo los PR pueden saltear; un push a `develop` decide `completo=true` sin mirar archivos."""
    texto = CI.read_text(encoding="utf-8")
    assert '"$EVENTO" != "pull_request"' in texto
