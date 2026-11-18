"""`scripts/calidad.sh` corre lo mismo que el CI (`IQ-06`, Issue de la Iteración 1)."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[3]
SCRIPT = RAIZ / "scripts" / "calidad.sh"
CI = yaml.safe_load((RAIZ / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))


def _comandos(job: str, saltear: tuple[str, ...] = ()) -> list[str]:
    """Los comandos `run:` de un job del CI, sin los de instalación."""
    pasos = CI["jobs"][job]["steps"]
    corridas = [p["run"].strip() for p in pasos if "run" in p]
    return [c for c in corridas if not c.startswith(saltear)]


class TestScriptDeCalidad:
    def test_tiene_sintaxis_valida_y_es_ejecutable(self) -> None:
        assert subprocess.run(["bash", "-n", str(SCRIPT)], check=False).returncode == 0
        assert SCRIPT.stat().st_mode & 0o111

    def test_la_ayuda_funciona_y_no_ejecuta_nada(self) -> None:
        r = subprocess.run(
            [str(SCRIPT), "--ayuda"], capture_output=True, text=True, check=False, timeout=30
        )
        assert r.returncode == 0
        assert "--completo" in r.stdout

    def test_rechaza_una_opcion_desconocida(self) -> None:
        r = subprocess.run(
            [str(SCRIPT), "--nada"], capture_output=True, text=True, check=False, timeout=30
        )
        assert r.returncode == 2

    def test_incluye_todos_los_comandos_del_lint_backend_del_ci(self) -> None:
        texto = SCRIPT.read_text(encoding="utf-8")
        for comando in _comandos("lint-backend", saltear=("uv sync",)):
            assert comando in texto, comando

    def test_incluye_el_designreviewer_del_ci(self) -> None:
        texto = SCRIPT.read_text(encoding="utf-8")
        for comando in _comandos("design-review", saltear=("uv sync",)):
            assert comando in texto, comando

    def test_incluye_los_comandos_del_frontend_del_ci(self) -> None:
        texto = SCRIPT.read_text(encoding="utf-8")
        for comando in _comandos("lint-frontend", saltear=("npm ci",)):
            assert comando in texto, comando

    def test_incluye_pytest_con_cobertura_como_el_ci(self) -> None:
        texto = SCRIPT.read_text(encoding="utf-8")
        assert any(c in texto for c in _comandos("test", saltear=("uv sync", "uv run alembic")))

    def test_pytest_exige_una_base_de_tests(self) -> None:
        assert re.search(r"\*_test\)", SCRIPT.read_text(encoding="utf-8"))


class TestJobDeSeguridadDelCi:
    def test_existe_y_no_bloquea(self) -> None:
        job = CI["jobs"]["seguridad"]
        pasos_de_auditoria = [p for p in job["steps"] if "audit" in p.get("run", "")]
        assert len(pasos_de_auditoria) == 2
        assert all(p.get("continue-on-error") is True for p in pasos_de_auditoria)

    def test_audita_solo_produccion(self) -> None:
        texto = " ".join(p.get("run", "") for p in CI["jobs"]["seguridad"]["steps"])
        assert "--no-dev" in texto
        assert "--omit=dev" in texto

    def test_ningun_check_obligatorio_depende_del_job(self) -> None:
        for nombre, job in CI["jobs"].items():
            necesidades = job.get("needs", [])
            necesidades = [necesidades] if isinstance(necesidades, str) else necesidades
            assert "seguridad" not in necesidades, nombre
