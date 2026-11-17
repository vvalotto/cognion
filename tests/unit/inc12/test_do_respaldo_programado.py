"""Respaldo programado y vigilado en `deploy/servidor/` (`DO-02`, Issue #646)."""

from __future__ import annotations

import os
import shutil
import stat
import sys
import time
from pathlib import Path

from tests.unit.inc10._servidor import correr, preparar

AQUI = Path(__file__).resolve().parent
MARCA = "# cognion-respaldo"


def _con_crontab(tmp_path: Path, **estado) -> Path:
    """Carpeta del servidor con un `crontab` simulado en el PATH aislado."""
    carpeta = preparar(tmp_path, **estado)
    destino = tmp_path / "bin" / "crontab"
    destino.write_text(f"#!{sys.executable}\n" + (AQUI / "_crontab_falso.py").read_text())
    destino.chmod(destino.stat().st_mode | stat.S_IXUSR)
    return carpeta


def _tabla(tmp_path: Path) -> list[str]:
    ruta = tmp_path / "crontab.txt"
    return ruta.read_text().splitlines() if ruta.exists() else []


def _dump(carpeta: Path, horas: float) -> None:
    """Un respaldo con la antigüedad pedida."""
    destino = carpeta / "respaldos"
    destino.mkdir(exist_ok=True)
    archivo = destino / f"cognion-{int(time.time() - horas * 3600)}.dump"
    archivo.write_bytes(b"PGDMP-FALSO\n")
    marca = time.time() - horas * 3600
    os.utime(archivo, (marca, marca))


class TestProgramarRespaldo:
    def test_deja_una_linea_marcada_con_el_respaldo_diario(self, tmp_path: Path) -> None:
        carpeta = _con_crontab(tmp_path)

        r = correr(tmp_path, carpeta, "cognion.sh", "programar-respaldo")

        assert r.returncode == 0, r.stderr
        lineas = [linea for linea in _tabla(tmp_path) if MARCA in linea]
        assert len(lineas) == 1
        assert lineas[0].startswith("0 3 * * * cd ")
        assert "./respaldar.sh" in lineas[0]

    def test_es_idempotente_y_conserva_las_otras_lineas(self, tmp_path: Path) -> None:
        carpeta = _con_crontab(tmp_path)
        (tmp_path / "crontab.txt").write_text("30 4 * * 1 /usr/bin/otra-tarea\n")

        correr(tmp_path, carpeta, "cognion.sh", "programar-respaldo")
        correr(tmp_path, carpeta, "cognion.sh", "programar-respaldo")

        tabla = _tabla(tmp_path)
        assert sum(MARCA in linea for linea in tabla) == 1
        assert "30 4 * * 1 /usr/bin/otra-tarea" in tabla

    def test_respeta_el_horario_y_la_carpeta_configurados(self, tmp_path: Path) -> None:
        carpeta = _con_crontab(tmp_path)

        correr(
            tmp_path,
            carpeta,
            "cognion.sh",
            "programar-respaldo",
            COGNION_RESPALDO_HORARIO="15 2 * * *",
            COGNION_RESPALDOS="/srv/respaldos",
        )

        linea = next(x for x in _tabla(tmp_path) if MARCA in x)
        assert linea.startswith("15 2 * * * ")
        assert "COGNION_RESPALDOS=/srv/respaldos ./respaldar.sh" in linea

    def test_sin_crontab_avisa_y_falla_el_subcomando(self, tmp_path: Path) -> None:
        carpeta = preparar(tmp_path)

        r = correr(tmp_path, carpeta, "cognion.sh", "programar-respaldo")

        assert r.returncode != 0
        assert "crontab" in r.stderr

    def test_desplegar_deja_programado_el_respaldo(self, tmp_path: Path) -> None:
        carpeta = _con_crontab(tmp_path)

        r = correr(tmp_path, carpeta, "cognion.sh", "desplegar", "cognion:nueva")

        assert r.returncode == 0, r.stderr
        assert any(MARCA in linea for linea in _tabla(tmp_path))

    def test_desplegar_no_falla_si_no_hay_crontab(self, tmp_path: Path) -> None:
        carpeta = preparar(tmp_path)

        r = correr(tmp_path, carpeta, "cognion.sh", "desplegar", "cognion:nueva")

        assert r.returncode == 0, r.stderr


class TestEstadoInformaLosRespaldos:
    def test_un_respaldo_reciente_se_informa_sin_aviso(self, tmp_path: Path) -> None:
        carpeta = _con_crontab(tmp_path)
        correr(tmp_path, carpeta, "cognion.sh", "programar-respaldo")
        _dump(carpeta, horas=2)

        r = correr(tmp_path, carpeta, "cognion.sh", "estado")

        assert "Último respaldo:" in r.stdout
        assert "hace 2 h" in r.stdout
        assert "AVISO: el último respaldo" not in r.stdout
        assert "Respaldo diario:  programado" in r.stdout

    def test_un_respaldo_vencido_avisa(self, tmp_path: Path) -> None:
        carpeta = _con_crontab(tmp_path)
        _dump(carpeta, horas=50)

        r = correr(tmp_path, carpeta, "cognion.sh", "estado")

        assert "AVISO: el último respaldo tiene más de 36 h" in r.stdout

    def test_el_limite_de_antiguedad_se_configura(self, tmp_path: Path) -> None:
        carpeta = _con_crontab(tmp_path)
        _dump(carpeta, horas=5)

        r = correr(tmp_path, carpeta, "cognion.sh", "estado", COGNION_RESPALDO_MAX_HORAS="4")

        assert "tiene más de 4 h" in r.stdout

    def test_sin_respaldos_avisa(self, tmp_path: Path) -> None:
        carpeta = _con_crontab(tmp_path)

        r = correr(tmp_path, carpeta, "cognion.sh", "estado")

        assert "AVISO: no hay respaldos" in r.stdout

    def test_sin_cron_avisa_que_no_esta_programado(self, tmp_path: Path) -> None:
        carpeta = _con_crontab(tmp_path)
        _dump(carpeta, horas=1)

        r = correr(tmp_path, carpeta, "cognion.sh", "estado")

        assert "el respaldo diario no está programado" in r.stdout
