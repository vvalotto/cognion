"""`docker` simulado para los tests de US-8.6.4.

No es un test: el helper lo copia a un PATH aislado con el nombre `docker`. Registra cada llamada y
la imagen que usaría `compose` (la de la variable `COGNION_IMAGE` o la del `.env`, igual que hace
Compose). Un archivo de estado decide qué falla.
"""

import os
import sys

from _comun_falso import cargar, registrar  # pylint: disable=import-error  # junto al simulador


def _imagen_efectiva() -> str | None:
    if os.environ.get("COGNION_IMAGE"):
        return os.environ["COGNION_IMAGE"]
    with open(".env", encoding="utf-8") as archivo:
        for linea in archivo:
            if linea.startswith("COGNION_IMAGE="):
                return linea.strip().split("=", 1)[1]
    return None


def _compose(sub: list[str], estado: dict) -> int:
    if "run" in sub and "alembic" in sub:
        registrar(f"MIGRAR imagen={_imagen_efectiva()}")
        return 1 if estado.get("migracion_falla") else 0
    if "up" in sub and "app" in sub:
        imagen = _imagen_efectiva()
        registrar(f"UP_APP imagen={imagen}")
        return 1 if imagen in estado.get("no_saludables", []) else 0
    if "up" in sub and "db" in sub:
        registrar("UP_DB")
        return 0
    registrar("COMPOSE " + " ".join(sub))
    return 0


def main(args: list[str]) -> int:
    """Despacha el comando simulado y devuelve el código de salida."""
    estado = cargar()
    if args[:2] == ["image", "inspect"]:
        return 0 if args[2] in estado.get("imagenes_locales", []) else 1
    if args[0] == "pull":
        registrar("PULL " + args[1])
        return 1 if estado.get("pull_falla") else 0
    if args[0] == "compose":
        return _compose(args[1:], estado)
    registrar("DOCKER " + " ".join(args))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
