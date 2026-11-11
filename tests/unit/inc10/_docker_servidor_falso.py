"""`docker` simulado para los tests de US-10.2.2 (servidor Linux con Docker).

No es un test: `_servidor.instalar` lo copia a un PATH aislado con el nombre `docker`. Extiende al simulador de US-8.6.4
(`_docker_falso`, que resuelve `pull`, `image inspect` y `compose run/up`) con lo que usan el respaldo y la restauración:
`docker compose exec -T db <comando>` y `docker compose stop/version`. Un archivo de estado (`FAKE_ESTADO`) decide qué falla.
"""

import os
import sys

import _docker_falso  # pylint: disable=import-error  # junto al simulador
from _comun_falso import cargar, registrar  # pylint: disable=import-error

CONTENIDO_DUMP = b"PGDMP-FALSO\n"


def _exec_db(comando: list[str], estado: dict) -> int:
    """`docker compose exec -T db <comando>`."""
    registrar("EXEC " + " ".join(comando))
    programa = comando[0]
    if programa == "pg_dump":
        if estado.get("pg_dump_falla"):
            sys.stderr.write("pg_dump: error simulado\n")
            return 1
        if not estado.get("dump_vacio"):
            sys.stdout.buffer.write(CONTENIDO_DUMP)
        return 0
    if programa == "pg_restore":
        contenido = sys.stdin.buffer.read()
        if "--list" in comando:
            legible = contenido.startswith(b"PGDMP") and not estado.get("dump_ilegible")
            return 0 if legible else 1
        return 1 if estado.get("restauracion_falla") else 0
    if programa == "psql":
        base = comando[comando.index("-d") + 1] if "-d" in comando else ""
        print(42 if base == "cognion" else 40)
        return 0
    return 0  # createdb, dropdb


def main(args: list[str]) -> int:
    """Despacha el comando simulado y devuelve el código de salida."""
    estado = cargar()
    if args[:2] == ["compose", "version"]:
        return 1 if estado.get("sin_compose") else 0
    if args[:2] == ["compose", "exec"]:
        resto = args[2:]
        if resto[:1] == ["-T"]:
            resto = resto[1:]
        return _exec_db(resto[1:], estado)  # resto[0] es el servicio ("db")
    if args[:2] == ["compose", "stop"]:
        registrar("STOP " + " ".join(args[2:]))
        return 0
    if args[:2] == ["compose", "up"] and "app" in args and os.environ.get("FAKE_LOG"):
        pass  # lo resuelve el simulador base (UP_APP con la imagen efectiva)
    return _docker_falso.main(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
