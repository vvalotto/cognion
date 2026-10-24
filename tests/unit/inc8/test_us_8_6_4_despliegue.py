"""Despliegue y rollback de `cognion.sh` (US-8.6.4), con `docker` simulado (`_docker_falso.py`).

El ejecutable falso registra cada llamada y la imagen que usaría `compose`. Un archivo de estado
decide qué falla: la descarga, la migración o la salud de una imagen.
"""

import json
import shutil
import stat
import subprocess
from pathlib import Path

from tests.unit.inc8._simuladores import GCP, instalar_basicos, instalar_simulador


def _preparar(tmp_path: Path, env_extra: str = "", con_docker: bool = True, **estado) -> Path:
    """Copia cognion.sh a una carpeta aislada con su .env y un docker falso en un PATH mínimo."""
    carpeta = tmp_path / "gcp"
    carpeta.mkdir()
    shutil.copy(GCP / "cognion.sh", carpeta / "cognion.sh")
    env = carpeta / ".env"
    env.write_text(
        "COGNION_DOMINIO=cognion-fiuner.duckdns.org\nCOGNION_IMAGE=cognion:vieja\n" + env_extra
    )
    env.chmod(0o600)
    bin_ = tmp_path / "bin"
    instalar_basicos(bin_)
    if con_docker:
        instalar_simulador(bin_, "docker", "_docker_falso.py")
    (tmp_path / "estado.json").write_text(json.dumps(estado))
    return carpeta


def _correr(tmp_path: Path, carpeta: Path, *args: str):
    entorno = {
        "PATH": str(tmp_path / "bin"),
        "FAKE_LOG": str(tmp_path / "llamadas.log"),
        "FAKE_ESTADO": str(tmp_path / "estado.json"),
        "HOME": str(tmp_path),
    }
    return subprocess.run(
        ["bash", str(carpeta / "cognion.sh"), *args],
        capture_output=True,
        text=True,
        env=entorno,
        check=False,
    )  # noqa: S603,S607


def _log(tmp_path: Path) -> list[str]:
    ruta = tmp_path / "llamadas.log"
    return ruta.read_text().splitlines() if ruta.exists() else []


def _env(carpeta: Path) -> dict[str, str]:
    lineas = (carpeta / ".env").read_text().splitlines()
    return dict(linea.split("=", 1) for linea in lineas if "=" in linea)


# ---------------------------------------------------------------- despliegue exitoso


def test_despliegue_exitoso_en_el_orden_correcto(tmp_path: Path) -> None:
    """Baja, migra con la imagen NUEVA, reemplaza la aplicación y guarda la anterior (rollback)."""
    carpeta = _preparar(tmp_path)
    r = _correr(tmp_path, carpeta, "desplegar", "ghcr.io/vvalotto/cognion:v0.8.2")
    assert r.returncode == 0, r.stderr
    ll = _log(tmp_path)
    pasos = [
        next(i for i, x in enumerate(ll) if x.startswith(p)) for p in ("PULL", "MIGRAR", "UP_APP")
    ]
    assert pasos == sorted(pasos)
    assert "MIGRAR imagen=ghcr.io/vvalotto/cognion:v0.8.2" in ll  # migra con la imagen nueva
    assert "UP_APP imagen=ghcr.io/vvalotto/cognion:v0.8.2" in ll
    env = _env(carpeta)
    assert env["COGNION_IMAGE"] == "ghcr.io/vvalotto/cognion:v0.8.2"
    assert env["COGNION_IMAGE_ANTERIOR"] == "cognion:vieja"


def test_la_migracion_corre_antes_de_reemplazar_la_aplicacion(tmp_path: Path) -> None:
    """La versión vieja sigue sirviendo mientras se migra: el .env aún no cambió cuando migra."""
    carpeta = _preparar(tmp_path, migracion_falla=True)
    _correr(tmp_path, carpeta, "desplegar", "cognion:nueva")
    assert _env(carpeta)["COGNION_IMAGE"] == "cognion:vieja"


def test_el_env_conserva_los_permisos_600(tmp_path: Path) -> None:
    """Reescribir el .env no abre los permisos de los secretos."""
    carpeta = _preparar(tmp_path)
    _correr(tmp_path, carpeta, "desplegar", "cognion:nueva")
    assert stat.S_IMODE((carpeta / ".env").stat().st_mode) == 0o600
    assert [
        p.name for p in carpeta.iterdir() if p.name.startswith(".env.")
    ] == []  # sin temporales sueltos


def test_una_imagen_cargada_a_mano_no_se_baja(tmp_path: Path) -> None:
    """`docker load` deja la imagen local: no hay nada que bajar."""
    carpeta = _preparar(tmp_path, imagenes_locales=["cognion:ci"])
    r = _correr(tmp_path, carpeta, "desplegar", "cognion:ci")
    assert r.returncode == 0, r.stderr
    assert not any(x.startswith("PULL") for x in _log(tmp_path))


# ---------------------------------------------------------------- fallos


def test_si_no_puede_bajar_la_imagen_no_toca_nada(tmp_path: Path) -> None:
    """Escenario 7: sin conexión al registro, error claro y la versión actual sigue sirviendo."""
    carpeta = _preparar(tmp_path, pull_falla=True)
    r = _correr(tmp_path, carpeta, "desplegar", "ghcr.io/vvalotto/cognion:v0.8.2")
    assert r.returncode != 0
    assert "No pude bajar la imagen" in r.stderr and "Traceback" not in r.stderr
    ll = _log(tmp_path)
    assert not any(x.startswith(("MIGRAR", "UP_APP")) for x in ll)
    assert _env(carpeta)["COGNION_IMAGE"] == "cognion:vieja"


def test_si_la_migracion_falla_se_aborta_y_la_anterior_sigue_sirviendo(tmp_path: Path) -> None:
    """Escenario 6: no se reemplaza la aplicación ni se cambia la versión guardada."""
    carpeta = _preparar(tmp_path, migracion_falla=True)
    r = _correr(tmp_path, carpeta, "desplegar", "cognion:nueva")
    assert r.returncode != 0
    assert "La migración falló" in r.stderr and "cognion:vieja" in r.stderr
    assert not any(x.startswith("UP_APP") for x in _log(tmp_path))
    env = _env(carpeta)
    assert env["COGNION_IMAGE"] == "cognion:vieja" and "COGNION_IMAGE_ANTERIOR" not in env


def test_si_la_version_nueva_no_responde_vuelve_sola_a_la_anterior(tmp_path: Path) -> None:
    """Escenario 5: rollback automático; el .env vuelve exactamente a como estaba."""
    carpeta = _preparar(
        tmp_path,
        env_extra="COGNION_IMAGE_ANTERIOR=cognion:vieja0\n",
        no_saludables=["cognion:rota"],
    )
    r = _correr(tmp_path, carpeta, "desplegar", "cognion:rota")
    assert r.returncode != 0
    assert "Volviendo a cognion:vieja" in r.stderr and "Rollback hecho" in r.stderr
    ups = [x for x in _log(tmp_path) if x.startswith("UP_APP")]
    assert ups == ["UP_APP imagen=cognion:rota", "UP_APP imagen=cognion:vieja"]
    env = _env(carpeta)
    assert env["COGNION_IMAGE"] == "cognion:vieja"
    assert env["COGNION_IMAGE_ANTERIOR"] == "cognion:vieja0"  # no apunta a la rota


def test_si_tampoco_responde_la_anterior_lo_dice(tmp_path: Path) -> None:
    """Si el rollback también falla, avisa con claridad en lugar de fingir que sirve."""
    carpeta = _preparar(tmp_path, no_saludables=["cognion:rota", "cognion:vieja"])
    r = _correr(tmp_path, carpeta, "desplegar", "cognion:rota")
    assert r.returncode != 0
    assert "tampoco la versión anterior respondió" in r.stderr


# ---------------------------------------------------------------- respaldo previo


def test_si_hay_respaldar_sh_se_ejecuta_antes_de_migrar(tmp_path: Path) -> None:
    """El respaldo previo corre antes de tocar la base."""
    carpeta = _preparar(tmp_path)
    script = carpeta / "respaldar.sh"
    script.write_text(f'#!/usr/bin/env bash\necho "RESPALDO" >> "{tmp_path}/llamadas.log"\n')
    script.chmod(0o755)
    r = _correr(tmp_path, carpeta, "desplegar", "cognion:nueva")
    assert r.returncode == 0, r.stderr
    ll = _log(tmp_path)
    assert ll.index("RESPALDO") < next(i for i, x in enumerate(ll) if x.startswith("MIGRAR"))


def test_si_el_respaldo_falla_no_se_despliega(tmp_path: Path) -> None:
    """Sin respaldo no se migra ni se reemplaza nada."""
    carpeta = _preparar(tmp_path)
    script = carpeta / "respaldar.sh"
    script.write_text("#!/usr/bin/env bash\nexit 1\n")
    script.chmod(0o755)
    r = _correr(tmp_path, carpeta, "desplegar", "cognion:nueva")
    assert r.returncode != 0 and "El respaldo previo falló" in r.stderr
    assert not any(x.startswith(("MIGRAR", "UP_APP")) for x in _log(tmp_path))


def test_sin_respaldar_sh_avisa_y_sigue(tmp_path: Path) -> None:
    """Hasta que exista US-8.6.5 se despliega con un aviso explícito."""
    carpeta = _preparar(tmp_path)
    r = _correr(tmp_path, carpeta, "desplegar", "cognion:nueva")
    assert r.returncode == 0
    assert "sin respaldo previo" in r.stderr


# ---------------------------------------------------------------- rollback manual y errores de uso


def test_rollback_manual_intercambia_las_versiones(tmp_path: Path) -> None:
    """`rollback` vuelve a la anterior y deja la actual como anterior (es reversible)."""
    carpeta = _preparar(tmp_path, env_extra="COGNION_IMAGE_ANTERIOR=cognion:previa\n")
    r = _correr(tmp_path, carpeta, "rollback")
    assert r.returncode == 0, r.stderr
    assert "solo la imagen" in r.stdout
    env = _env(carpeta)
    assert (
        env["COGNION_IMAGE"] == "cognion:previa"
        and env["COGNION_IMAGE_ANTERIOR"] == "cognion:vieja"
    )
    assert "UP_APP imagen=cognion:previa" in _log(tmp_path)


def test_rollback_sin_version_anterior_falla_con_mensaje(tmp_path: Path) -> None:
    """Sin una versión anterior guardada no hay a dónde volver."""
    carpeta = _preparar(tmp_path)
    r = _correr(tmp_path, carpeta, "rollback")
    assert r.returncode != 0
    assert "No hay una versión anterior" in r.stderr
    assert not any(x.startswith("UP_APP") for x in _log(tmp_path))


def test_desplegar_sin_imagen_falla_con_ejemplo(tmp_path: Path) -> None:
    """Sin argumento muestra cómo se usa."""
    carpeta = _preparar(tmp_path)
    r = _correr(tmp_path, carpeta, "desplegar")
    assert r.returncode != 0 and "Indicá la imagen" in r.stderr and "ghcr.io" in r.stderr


def test_sin_docker_falla_sin_traza(tmp_path: Path) -> None:
    """Sin Docker instalado, error claro."""
    carpeta = _preparar(tmp_path, con_docker=False)
    r = _correr(tmp_path, carpeta, "desplegar", "cognion:nueva")
    assert r.returncode != 0 and "Falta docker" in r.stderr and "Traceback" not in r.stderr


def test_el_resto_de_los_subcomandos_no_cambia() -> None:
    """Los subcomandos de US-8.6.2 siguen presentes (CI verifica `iniciar` de punta a punta)."""
    texto = (GCP / "cognion.sh").read_text()
    for subcomando in ("iniciar)", "migrar)", "administrador)", "estado)", "logs)", "detener)"):
        assert subcomando in texto
