"""Bootstrap del primer Administrador del sistema (fuera del producto — ver ADR-016).

Uso:
    ADMIN_NOMBRE="Nombre Apellido" ADMIN_EMAIL=admin@fiuner.edu.ar ADMIN_PASSWORD=... \
        .venv/bin/python scripts/seed_admin.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.identidad.entities.errors import EmailYaRegistrado  # noqa: E402
from src.identidad.entities.usuario import TipoPerfil  # noqa: E402
from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher  # noqa: E402
from src.identidad.interface_adapters.gateways.usuario_repository import (  # noqa: E402
    SQLAlchemyUsuarioRepository,
)
from src.identidad.use_cases.crear_usuario import CrearUsuarioUseCase  # noqa: E402
from src.shared.frameworks.db import SessionLocal  # noqa: E402


async def main() -> None:
    nombre = os.environ["ADMIN_NOMBRE"]
    email = os.environ["ADMIN_EMAIL"]
    password = os.environ["ADMIN_PASSWORD"]

    async with SessionLocal() as session:
        repo = SQLAlchemyUsuarioRepository(session)
        hasher = BcryptPasswordHasher()
        use_case = CrearUsuarioUseCase(repo, hasher)
        try:
            usuario, _evento = await use_case.execute(
                nombre, email, password, TipoPerfil.ADMINISTRADOR
            )
        except EmailYaRegistrado:
            print(f"Ya existe un Usuario con email '{email}' — no se crea de nuevo.")
            return

    print(f"Administrador creado: {usuario.id} ({usuario.email})")


if __name__ == "__main__":
    asyncio.run(main())
