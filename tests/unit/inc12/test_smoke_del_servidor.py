"""El smoke del CI prueba `deploy/servidor/`, la variante que se entrega (`DO-03`, Issue #665)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[3]
SMOKE = yaml.safe_load(
    (RAIZ / ".github" / "workflows" / "imagen-smoke.yml").read_text(encoding="utf-8")
)
SCRIPT = RAIZ / "tests" / "uat" / "inc12" / "verificar_servidor.sh"


class TestSmokeDelServidor:
    def test_hay_un_job_que_levanta_deploy_servidor(self) -> None:
        corridas = " ".join(p.get("run", "") for p in SMOKE["jobs"]["servidor"]["steps"])
        assert "deploy/servidor/cognion.sh iniciar" in corridas
        assert "tests/uat/inc12/verificar_servidor.sh" in corridas

    def test_el_smoke_de_gcp_sigue_corriendo(self) -> None:
        corridas = " ".join(p.get("run", "") for p in SMOKE["jobs"]["smoke"]["steps"])
        assert "deploy/gcp/cognion.sh iniciar" in corridas

    def test_se_dispara_al_cambiar_el_script_de_verificacion(self) -> None:
        assert "tests/uat/inc12/verificar_servidor.sh" in SMOKE[True]["push"]["paths"]

    def test_el_script_tiene_sintaxis_valida_y_es_ejecutable(self) -> None:
        assert subprocess.run(["bash", "-n", str(SCRIPT)], check=False).returncode == 0
        assert SCRIPT.stat().st_mode & 0o111

    def test_verifica_lo_propio_del_paquete_que_se_entrega(self) -> None:
        texto = SCRIPT.read_text(encoding="utf-8")
        for esperado in (
            "respaldar.sh",
            "restaurar.sh",
            "desplegar",
            "rollback",
            "programar-respaldo",
            "health/ready",
        ):
            assert esperado in texto, esperado
