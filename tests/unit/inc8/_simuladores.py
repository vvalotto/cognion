"""Utilidades de los tests de US-8.6.4: PATH aislado con ejecutables simulados y estado de `gcloud`.

Los ejecutables falsos (`_gcloud_falso.py`, `_docker_falso.py`) se copian a una carpeta propia del
test, junto con enlaces a las utilidades básicas; esa carpeta es el único PATH de los scripts.
Así ningún `gcloud` o `docker` real puede colarse, aunque estén instalados en la máquina.
"""

import json
import shutil
import stat
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
GCP = RAIZ / "deploy" / "gcp"
AQUI = Path(__file__).resolve().parent
BASICOS = (
    "bash sh env dirname sed grep cut head tail tr seq sleep cat mktemp chmod mv rm awk wc id "
    "touch tee date basename sort uniq mkdir tar gzip ls"
).split()


def instalar_basicos(carpeta: Path) -> None:
    """Enlaza las utilidades básicas que usan los scripts."""
    carpeta.mkdir(exist_ok=True)
    for programa in BASICOS:
        destino = carpeta / programa
        real = shutil.which(programa)
        if real and not destino.exists():
            destino.symlink_to(real)


def instalar_simulador(carpeta: Path, nombre: str, fuente: str) -> None:
    """Copia un ejecutable simulado (con su `#!` apuntando al Python actual) como `nombre`."""
    destino = carpeta / nombre
    destino.write_text(f"#!{sys.executable}\n" + (AQUI / fuente).read_text(encoding="utf-8"))
    destino.chmod(destino.stat().st_mode | stat.S_IXUSR)
    shutil.copy(AQUI / "_comun_falso.py", carpeta / "_comun_falso.py")  # lo importa el simulador


def crear_entorno(tmp_path: Path, con_gcloud: bool = True) -> dict:
    """Entorno de un script que usa `gcloud`: PATH mínimo y las rutas del registro y del estado."""
    carpeta = tmp_path / "bin"
    instalar_basicos(carpeta)
    if con_gcloud:
        instalar_simulador(carpeta, "gcloud", "_gcloud_falso.py")
    return {
        "PATH": str(carpeta),
        "FAKE_LOG": str(tmp_path / "llamadas.log"),
        "FAKE_ESTADO": str(tmp_path / "estado.json"),
        "FAKE_STDIN": str(tmp_path / "stdin.bin"),
        "HOME": str(tmp_path),
    }


def escribir_estado(tmp_path: Path, **cambios) -> None:
    """Estado inicial de la nube simulada: un proyecto vacío, salvo lo que se indique."""
    base = {
        "cuenta": "vvalotto@gmail.com",
        "proyecto": False,
        "facturacion": False,
        "apis": [],
        "presupuestos": [],
        "reglas": ["default-allow-rdp", "default-allow-ssh", "default-allow-icmp"],
        "ips": [],
        "vms": [],
    }
    base.update(cambios)
    (tmp_path / "estado.json").write_text(json.dumps(base))


def estado_con_proyecto(tmp_path: Path, **cambios) -> None:
    """Estado de un proyecto que ya existe, con facturación y APIs habilitadas pero sin recursos."""
    escribir_estado(
        tmp_path,
        proyecto=True,
        facturacion=True,
        apis=["compute.googleapis.com", "billingbudgets.googleapis.com"],
        **cambios,
    )


def estado_completo(tmp_path: Path, **cambios) -> None:
    """Estado de la nube con todo lo de la prueba ya creado."""
    recursos = {
        "presupuestos": ["cognion-prueba"],
        "reglas": ["default-allow-ssh", "default-allow-icmp", "cognion-web"],
        "ips": ["cognion-ip"],
        "vms": ["cognion-vm"],
    }
    recursos.update(cambios)
    estado_con_proyecto(tmp_path, **recursos)


def correr_script(
    tmp_path: Path,
    script: str,
    *args: str,
    entrada: str = "",
    extra: dict | None = None,
    con_gcloud: bool = True,
):
    """Ejecuta un script de `deploy/gcp/` con la nube simulada."""
    env = crear_entorno(tmp_path, con_gcloud)
    env.update({"PROYECTO": "cognion-prueba-2410", "CUENTA_FACTURACION": "019D68-E7FC7F-247D34"})
    env.update(extra or {})
    return subprocess.run(  # noqa: S603
        ["bash", str(GCP / script), *args],  # noqa: S607
        input=entrada,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def leer_llamadas(tmp_path: Path) -> list[str]:
    """Llamadas registradas por el ejecutable simulado, en orden."""
    ruta = tmp_path / "llamadas.log"
    return ruta.read_text().splitlines() if ruta.exists() else []


def llamadas_que_mutan(llamadas: list[str]) -> list[str]:
    """Llamadas que crean, borran, vinculan o habilitan algo."""
    verbos = (" create", " delete", " link", " enable")
    return [x for x in llamadas if any(v in x for v in verbos)]


def buscar_indice(llamadas: list[str], fragmento: str) -> int:
    """Posición de la primera llamada que contiene el fragmento."""
    for i, linea in enumerate(llamadas):
        if fragmento in linea:
            return i
    raise AssertionError(f"no se encontró '{fragmento}' en {llamadas}")
