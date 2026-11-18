"""La cobertura mide todo `src/` y los umbrales bloquean (`VT-01`, `VT-02`, Issue #665)."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[3]
PYPROJECT = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))
CI = yaml.safe_load((RAIZ / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))


def _pasos(job: str) -> list[str]:
    return [p["run"] for p in CI["jobs"][job]["steps"] if "run" in p]


class TestCoberturaDelBackend:
    def test_no_omite_frameworks(self) -> None:
        omitidos = PYPROJECT["tool"]["coverage"]["run"]["omit"]
        assert not any("frameworks" in patron for patron in omitidos)

    def test_el_umbral_total_bloquea(self) -> None:
        assert PYPROJECT["tool"]["coverage"]["report"]["fail_under"] >= 90

    def test_el_ci_exige_un_umbral_por_cada_parte(self) -> None:
        pasos = " ".join(_pasos("test"))
        interna = re.search(
            r"coverage report --omit='src/\*/frameworks/\*' --fail-under=(\d+)", pasos
        )
        frameworks = re.search(
            r"coverage report --include='src/\*/frameworks/\*' --fail-under=(\d+)", pasos
        )
        assert interna and int(interna.group(1)) >= 95
        assert frameworks and int(frameworks.group(1)) >= 80

    def test_el_script_local_exige_los_mismos_umbrales(self) -> None:
        script = (RAIZ / "scripts" / "calidad.sh").read_text(encoding="utf-8")
        pasos = "\n".join(_pasos("test"))
        for umbral in re.findall(r"coverage report [^\n]*", pasos):
            assert umbral.strip() in script, umbral


class TestCoberturaYE2EDelFrontend:
    def test_vitest_corre_con_los_umbrales_de_cobertura(self) -> None:
        assert any("npm run test:coverage" in paso for paso in _pasos("lint-frontend"))

    def test_hay_un_job_de_playwright_con_su_base(self) -> None:
        job = CI["jobs"]["e2e"]
        assert any("npm run test:e2e" in paso for paso in _pasos("e2e"))
        assert "postgres" in job["services"]
        assert "DATABASE_URL" in job["env"]

    def test_el_teardown_del_e2e_limpia_la_base_que_se_uso(self) -> None:
        script = (RAIZ / "tests" / "uat" / "inc6" / "limpiar_uat.sh").read_text(encoding="utf-8")
        assert "${DATABASE_URL" in script
