"""Utilidades de los tests de `deploy/servidor/` (US-10.2.2): carpeta aislada, PATH con ejecutables simulados y corrida."""

from __future__ import annotations

import json
import shutil
import stat
import subprocess
import sys
from pathlib import Path

from tests.unit.inc8._simuladores import AQUI as AQUI_INC8
from tests.unit.inc8._simuladores import instalar_basicos

RAIZ = Path(__file__).resolve().parents[3]
SERVIDOR = RAIZ / "deploy" / "servidor"
AQUI = Path(__file__).resolve().parent
ARCHIVOS = ("cognion.sh", "salud.sh", "respaldar.sh", "restaurar.sh")
EXTRAS = ("du", "shasum", "sha256sum", "cp", "stat", "readlink", "expr")


def _instalar(bin_: Path, nombre: str, fuente: Path) -> None:
    destino = bin_ / nombre
    destino.write_text(f"#!{sys.executable}\n" + fuente.read_text(encoding="utf-8"))
    destino.chmod(destino.stat().st_mode | stat.S_IXUSR)


def preparar(tmp_path: Path, env: str = "", con_docker: bool = True, **estado) -> Path:
    """Copia los scripts a una carpeta aislada con su `.env`, un `docker`/`curl` falsos y un PATH mínimo."""
    carpeta = tmp_path / "servidor"
    carpeta.mkdir()
    for nombre in ARCHIVOS:
        shutil.copy(SERVIDOR / nombre, carpeta / nombre)
    (carpeta / ".env").write_text(
        "COGNION_DOMINIO=cognion.facultad.edu.ar\nCOGNION_IMAGE=cognion:vieja\n" + env
    )
    (carpeta / ".env").chmod(0o600)
    bin_ = tmp_path / "bin"
    instalar_basicos(bin_)
    for programa in EXTRAS:
        real = shutil.which(programa)
        if real and not (bin_ / programa).exists():
            (bin_ / programa).symlink_to(real)
    shutil.copy(AQUI_INC8 / "_comun_falso.py", bin_ / "_comun_falso.py")
    shutil.copy(AQUI_INC8 / "_docker_falso.py", bin_ / "_docker_falso.py")
    _instalar(bin_, "curl", AQUI / "_curl_servidor_falso.py")
    if con_docker:
        _instalar(bin_, "docker", AQUI / "_docker_servidor_falso.py")
    (tmp_path / "estado.json").write_text(json.dumps(estado))
    return carpeta


def correr(
    tmp_path: Path, carpeta: Path, script: str, *args: str, entrada: str | None = None, **entorno
):
    """Ejecuta un script de la carpeta con el PATH aislado."""
    return subprocess.run(  # noqa: S603
        ["bash", str(carpeta / script), *args],
        capture_output=True,
        text=True,
        input=entrada,
        env={
            "PATH": str(tmp_path / "bin"),
            "FAKE_LOG": str(tmp_path / "llamadas.log"),
            "FAKE_ESTADO": str(tmp_path / "estado.json"),
            "HOME": str(tmp_path),
            **{k: str(v) for k, v in entorno.items()},
        },
        check=False,
    )


def log(tmp_path: Path) -> list[str]:
    """Llamadas registradas por los ejecutables simulados."""
    ruta = tmp_path / "llamadas.log"
    return ruta.read_text().splitlines() if ruta.exists() else []


def leer_env(carpeta: Path) -> dict[str, str]:
    """El `.env` como diccionario."""
    lineas = (carpeta / ".env").read_text().splitlines()
    return dict(
        linea.split("=", 1) for linea in lineas if "=" in linea and not linea.startswith("#")
    )
