"""`crontab` simulado (no es un test): guarda la tabla en `crontab.txt`, junto al archivo de estado."""

import os
import sys
from pathlib import Path

tabla = Path(os.environ["FAKE_ESTADO"]).with_name("crontab.txt")
if sys.argv[1:] == ["-l"]:
    if not tabla.exists():
        sys.stderr.write("no crontab for test\n")
        sys.exit(1)
    sys.stdout.write(tabla.read_text())
elif sys.argv[1:] == ["-"]:
    tabla.write_text(sys.stdin.read())
else:
    sys.exit(2)
