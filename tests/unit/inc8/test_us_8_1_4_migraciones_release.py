"""Las migraciones son un paso de release, no del arranque de la app (US-8.1.4)."""

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


def test_la_app_no_ejecuta_alembic_al_arrancar() -> None:
    """Ningún módulo de `src/` importa Alembic: migrar es responsabilidad del release."""
    importadores = [
        ruta
        for ruta in (_RAIZ / "src").rglob("*.py")
        if "alembic" in ruta.read_text(encoding="utf-8").lower()
    ]
    assert importadores == []
