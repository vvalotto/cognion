"""Las migraciones son un paso de release, no del arranque de la app (US-8.1.4)."""

import tomllib
from pathlib import Path

_RAIZ = Path(__file__).resolve().parents[3]


def _dockerfile() -> str:
    return (_RAIZ / "Dockerfile").read_text(encoding="utf-8")


def test_la_imagen_incluye_alembic_y_las_migraciones() -> None:
    """Sin `alembic.ini` y `migrations/` en la imagen, el release no podría migrar."""
    dockerfile = _dockerfile()
    assert "COPY alembic.ini" in dockerfile
    assert "COPY migrations/" in dockerfile


def test_el_cmd_de_la_imagen_no_migra() -> None:
    """El arranque del contenedor es solo `uvicorn`."""
    lineas_cmd = [linea for linea in _dockerfile().splitlines() if linea.startswith("CMD")]
    assert len(lineas_cmd) == 1
    assert "uvicorn" in lineas_cmd[0]
    assert "alembic" not in lineas_cmd[0]


def test_fly_toml_declara_el_release_command() -> None:
    """Fly corre `alembic upgrade head` antes de reemplazar la versión en producción."""
    config = tomllib.loads((_RAIZ / "fly.toml").read_text(encoding="utf-8"))
    assert config["deploy"]["release_command"] == "uv run alembic upgrade head"


def test_fly_toml_expone_el_servicio_con_healthcheck() -> None:
    """El servicio HTTP escucha en 8000, fuerza HTTPS y usa `/health`."""
    servicio = tomllib.loads((_RAIZ / "fly.toml").read_text(encoding="utf-8"))["http_service"]
    assert servicio["internal_port"] == 8000
    assert servicio["force_https"] is True
    assert servicio["checks"][0]["path"] == "/health"


def test_la_app_no_ejecuta_alembic_al_arrancar() -> None:
    """Ningún módulo de `src/` importa Alembic: migrar es responsabilidad del release."""
    importadores = [
        ruta
        for ruta in (_RAIZ / "src").rglob("*.py")
        if "alembic" in ruta.read_text(encoding="utf-8").lower()
    ]
    assert importadores == []
