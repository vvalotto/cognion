"""Versión de Cognión, leída del archivo `VERSION` de la raíz del proyecto (`US-10.2.1`).

Es la única fuente de la versión: `pyproject.toml`, `frontend/package.json` y la versión de FastAPI deben
coincidir con ella (lo comprueba un test) y el CD exige que el tag `vX.Y.Z` sea igual a este número.
En la imagen Docker el archivo queda en `/app/VERSION`, que es la misma ubicación relativa a `src/`.
"""

from __future__ import annotations

from pathlib import Path

_ARCHIVO_VERSION = Path(__file__).resolve().parents[3] / "VERSION"


def obtener_version(archivo: Path = _ARCHIVO_VERSION) -> str:
    """Devuelve la versión (por ejemplo `1.0.0`), sin espacios ni salto de línea.

    Lanza `RuntimeError` si el archivo no existe o está vacío: arrancar sin saber la versión
    ocultaría un empaquetado mal hecho.
    """
    try:
        version = archivo.read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:
        raise RuntimeError(f"No se encontró el archivo de versión: {archivo}") from exc
    if not version:
        raise RuntimeError(f"El archivo de versión está vacío: {archivo}")
    return version
