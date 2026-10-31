"""`desplegar.sh` (desde la Mac) y comprobaciones estáticas de los scripts y del CI (US-8.6.4)."""

import shutil
import stat
import subprocess
from pathlib import Path

import pytest
import yaml

from tests.unit.inc8._simuladores import (
    GCP,
    RAIZ,
    correr_script,
    crear_entorno,
    escribir_estado,
    leer_llamadas,
)

# ---------------------------------------------------------------- desplegar.sh (desde la Mac)


def _copia_de_gcp(tmp_path: Path) -> Path:
    destino = tmp_path / "deploy" / "gcp"
    shutil.copytree(GCP, destino, ignore=shutil.ignore_patterns(".env"))
    (destino / ".env").write_text("SECRETO=no-debe-viajar\n")
    return destino


@pytest.mark.parametrize(
    ("entrada", "imagen"),
    [
        ("v0.8.2", "ghcr.io/vvalotto/cognion:v0.8.2"),
        ("ghcr.io/otro/imagen:v1", "ghcr.io/otro/imagen:v1"),
        ("cognion:ci", "cognion:ci"),
    ],
)
def test_desplegar_completa_la_version_a_una_imagen(
    tmp_path: Path, entrada: str, imagen: str
) -> None:
    """Una versión sola va a GHCR; una imagen completa se usa tal cual."""
    escribir_estado(tmp_path)
    carpeta = _copia_de_gcp(tmp_path)
    env = crear_entorno(tmp_path)
    env["PROYECTO"] = "cognion-prueba-2410"
    r = subprocess.run(
        ["bash", str(carpeta / "desplegar.sh"), entrada],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )  # noqa: S603,S607
    assert r.returncode == 0, r.stderr
    assert f"./cognion.sh desplegar '{imagen}'" in "\n".join(leer_llamadas(tmp_path))


def test_desplegar_no_envia_el_env_a_la_vm(tmp_path: Path) -> None:
    """La sincronización lleva la configuración, pero nunca el `.env` con los secretos."""
    escribir_estado(tmp_path)
    carpeta = _copia_de_gcp(tmp_path)
    assert (
        carpeta / ".env"
    ).exists()  # el .env existe en la copia: si viajara, se vería en el paquete
    env = crear_entorno(tmp_path)
    env["PROYECTO"] = "cognion-prueba-2410"
    r = subprocess.run(
        ["bash", str(carpeta / "desplegar.sh"), "v0.8.2"],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )  # noqa: S603,S607
    assert r.returncode == 0, r.stderr
    paquete = (
        tmp_path / "stdin.bin.1"
    )  # lo que recibió la primera llamada por SSH: la sincronización
    nombres = subprocess.run(
        ["tar", "tzf", str(paquete)], capture_output=True, text=True, check=True
    ).stdout.split()
    assert "gcp/docker-compose.yml" in nombres and "gcp/cognion.sh" in nombres
    assert "gcp/.env" not in nombres
    contenido = subprocess.run(
        ["tar", "xzOf", str(paquete)], capture_output=True, text=True, check=True
    ).stdout
    assert "no-debe-viajar" not in contenido


def test_desplegar_exige_proyecto_y_version(tmp_path: Path) -> None:
    """Sin proyecto o sin versión, error claro y sin llamar a la nube."""
    escribir_estado(tmp_path)
    sin_proyecto = correr_script(tmp_path, "desplegar.sh", "v0.8.2", extra={"PROYECTO": ""})
    assert sin_proyecto.returncode != 0 and "Falta PROYECTO" in sin_proyecto.stderr
    sin_version = correr_script(tmp_path, "desplegar.sh")
    assert sin_version.returncode != 0 and "Indicá la versión" in sin_version.stderr
    assert not any("compute ssh" in x for x in leer_llamadas(tmp_path))


# ---------------------------------------------------------------- estáticos


@pytest.mark.parametrize(
    "script", ["aprovisionar.sh", "destruir.sh", "desplegar.sh", "preparar-vm.sh", "cognion.sh"]
)
def test_los_scripts_tienen_sintaxis_valida_y_son_ejecutables(script: str) -> None:
    """`bash -n` y permiso de ejecución."""
    assert (
        subprocess.run(["bash", "-n", str(GCP / script)], check=False).returncode == 0
    )  # noqa: S603,S607
    assert (GCP / script).stat().st_mode & stat.S_IXUSR


def test_preparar_vm_verifica_la_huella_de_la_clave_de_docker() -> None:
    """Docker se instala del repositorio oficial y se aborta si la huella no coincide."""
    texto = (GCP / "preparar-vm.sh").read_text()
    assert 'HUELLA_DOCKER="9DC858229FC7DD38854AE2D88D81803C0EBFCD88"' in texto
    assert 'if [ "$HUELLA" != "$HUELLA_DOCKER" ]' in texto
    assert "https://download.docker.com/linux/debian/gpg" in texto
    assert "get.docker.com" not in texto
    assert "swapon --show" in texto and "/etc/fstab" in texto


CONDICION_ETIQUETA = "startsWith(github.ref, 'refs/tags/v')"


def _cd() -> dict:
    return yaml.safe_load((RAIZ / ".github" / "workflows" / "cd.yml").read_text())["jobs"][
        "build-and-deploy"
    ]


def test_la_publicacion_en_ci_ocurre_solo_con_etiquetas() -> None:
    """Escenario 4: el inicio de sesión y la publicación en GHCR solo corren para `vX.Y.Z`."""
    job = _cd()
    assert job["permissions"]["packages"] == "write"
    condicionados = [p for p in job["steps"] if p.get("if") == CONDICION_ETIQUETA]
    assert len(condicionados) == 2
    assert "GHCR" in " ".join(p["name"] for p in condicionados)


def test_la_imagen_publicada_lleva_la_version_y_el_commit_y_no_latest() -> None:
    """Se publica con la versión y `sha-<commit>`; nunca `latest` (haría ambiguo el rollback)."""
    texto = (RAIZ / ".github" / "workflows" / "cd.yml").read_text()
    assert "IMAGEN: ghcr.io/${{ github.repository }}" in texto
    assert "docker push" in texto and "${{ github.ref_name }}" in texto
    assert "sha-${{ github.sha }}" in texto
    assert ":latest" not in texto


def test_la_imagen_se_liga_al_repositorio_y_fly_sigue_comentado() -> None:
    """La etiqueta de origen liga el paquete al repositorio; Fly.io sigue comentado."""
    texto = (RAIZ / ".github" / "workflows" / "cd.yml").read_text()
    assert "org.opencontainers.image.source" in texto
    assert "# - name: Deploy a Fly.io" in texto
