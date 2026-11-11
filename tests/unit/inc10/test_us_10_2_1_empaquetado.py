"""Scripts de la Release (US-10.2.1): extracto del CHANGELOG y paquete de instalación."""

from __future__ import annotations

import os
import subprocess
import tarfile
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"

CHANGELOG = """# Changelog

## [Unreleased]

## [2.0.0] - 2026-12-01

Texto de la versión.

### Added
- Algo nuevo.

## [1.5.0] - 2026-11-01

### Fixed
- Algo viejo.

## [1.0.0] - Unreleased
"""


def _correr(
    script: str, *args: str, raiz: Path, **entorno: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPTS / script), *args],
        capture_output=True,
        text=True,
        env={**os.environ, "RAIZ": str(raiz), **entorno},
        check=False,
    )


@pytest.fixture
def proyecto(tmp_path: Path) -> Path:
    """Un proyecto mínimo con VERSION 2.0.0 y un CHANGELOG."""
    (tmp_path / "VERSION").write_text("2.0.0\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")
    return tmp_path


class TestExtraerNotas:
    """Escenario 8."""

    def test_devuelve_solo_la_seccion_pedida(self, proyecto: Path) -> None:
        resultado = _correr("extraer_notas.sh", "2.0.0", raiz=proyecto)

        assert resultado.returncode == 0
        assert "Algo nuevo." in resultado.stdout
        assert "Texto de la versión." in resultado.stdout
        assert "Algo viejo." not in resultado.stdout
        assert "## [" not in resultado.stdout

    def test_falla_si_la_version_no_tiene_seccion(self, proyecto: Path) -> None:
        resultado = _correr("extraer_notas.sh", "9.9.9", raiz=proyecto)

        assert resultado.returncode != 0
        assert "9.9.9" in resultado.stderr

    def test_falla_si_la_seccion_esta_vacia(self, proyecto: Path) -> None:
        resultado = _correr("extraer_notas.sh", "1.0.0", raiz=proyecto)

        assert resultado.returncode != 0

    def test_falla_sin_argumento(self, proyecto: Path) -> None:
        resultado = _correr("extraer_notas.sh", raiz=proyecto)

        assert resultado.returncode != 0


class TestEmpaquetarRelease:
    """Escenario 6."""

    def test_genera_el_paquete_con_los_archivos_obligatorios(
        self, proyecto: Path, tmp_path: Path
    ) -> None:
        salida = tmp_path / "dist"

        resultado = _correr("empaquetar_release.sh", "2.0.0", raiz=proyecto, SALIDA=str(salida))

        assert resultado.returncode == 0, resultado.stderr
        paquete = salida / "cognion-2.0.0-instalacion.tar.gz"
        assert resultado.stdout.strip() == str(paquete)
        with tarfile.open(paquete) as tar:
            nombres = set(tar.getnames())
        assert {"cognion-2.0.0/VERSION", "cognion-2.0.0/CHANGELOG.md"} <= nombres

    def test_incluye_lo_opcional_cuando_existe(self, proyecto: Path, tmp_path: Path) -> None:
        (proyecto / "docs").mkdir()
        (proyecto / "docs" / "INSTALACION.md").write_text("guía", encoding="utf-8")
        (proyecto / "deploy" / "servidor").mkdir(parents=True)
        (proyecto / "deploy" / "servidor" / "docker-compose.yml").write_text(
            "name: x", encoding="utf-8"
        )
        salida = tmp_path / "dist"

        _correr("empaquetar_release.sh", "2.0.0", raiz=proyecto, SALIDA=str(salida))

        with tarfile.open(salida / "cognion-2.0.0-instalacion.tar.gz") as tar:
            nombres = set(tar.getnames())
        assert "cognion-2.0.0/docs/INSTALACION.md" in nombres
        assert "cognion-2.0.0/deploy/servidor/docker-compose.yml" in nombres

    def test_falla_si_la_version_pedida_no_es_la_del_archivo(
        self, proyecto: Path, tmp_path: Path
    ) -> None:
        resultado = _correr(
            "empaquetar_release.sh", "3.0.0", raiz=proyecto, SALIDA=str(tmp_path / "dist")
        )

        assert resultado.returncode != 0
        assert "no coincide" in resultado.stderr
        assert not (tmp_path / "dist").exists()

    def test_falla_si_falta_un_archivo_obligatorio(self, proyecto: Path, tmp_path: Path) -> None:
        (proyecto / "CHANGELOG.md").unlink()

        resultado = _correr(
            "empaquetar_release.sh", "2.0.0", raiz=proyecto, SALIDA=str(tmp_path / "dist")
        )

        assert resultado.returncode != 0
        assert "CHANGELOG.md" in resultado.stderr
