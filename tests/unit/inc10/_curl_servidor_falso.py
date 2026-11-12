"""`curl` simulado: registra la dirección consultada y responde como `/api/health` (para `cognion.sh estado`)."""

import sys

from _comun_falso import registrar  # pylint: disable=import-error


def main(args: list[str]) -> int:
    """Registra la URL (último argumento) y devuelve cuerpo + código de estado."""
    registrar("CURL " + args[-1])
    sys.stdout.write('{"status":"ok"}\n200')
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
