"""Bootstrap del primer Administrador — envoltorio de compatibilidad (`ADR-016`, `US-8.1.5`).

La lógica vive en `src/identidad/frameworks/cli/bootstrap_administrador.py` (va en la imagen
Docker). Este archivo conserva la ruta histórica:

    ADMIN_NOMBRE="Nombre Apellido" ADMIN_EMAIL=admin@ejemplo.edu.ar \
        .venv/bin/python scripts/seed_admin.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.identidad.frameworks.cli.bootstrap_administrador import main  # noqa: E402

if __name__ == "__main__":
    main()
