"""Comando operativo: crea el primer Administrador (`ADR-016`, `US-8.1.5`).

Uso (en Fly: `fly ssh console -C "<comando>"`):

    ADMIN_NOMBRE="Nombre Apellido" ADMIN_EMAIL=admin@ejemplo.edu.ar
    uv run python -m src.identidad.frameworks.cli.bootstrap_administrador

La contraseña se toma de `ADMIN_PASSWORD` si está definida; si no, se pide por terminal sin eco y
**dos veces** (`US-ADJ-65`): como no se ve, un error de tipeo dejaría un Administrador inaccesible.
Nunca se acepta como argumento ni se imprime. Códigos de salida: 0 creado o ya existía un
Administrador operativo, 1 entrada inválida (incluidas tres confirmaciones que no coinciden),
2 sin contraseña ni terminal donde pedirla.
"""

from __future__ import annotations

import asyncio
import getpass
import os
import sys
from collections.abc import Callable, Mapping

from src.identidad.entities.errors import (
    AdministradorYaExiste,
    EmailYaRegistrado,
    PasswordDemasiadoCorta,
    PasswordSinComplejidadSuficiente,
)
from src.identidad.entities.ports.password_hasher_port import PasswordHasherPort
from src.identidad.entities.ports.usuario_repository_port import UsuarioRepositoryPort
from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher
from src.identidad.interface_adapters.gateways.usuario_repository import (
    SQLAlchemyUsuarioRepository,
)
from src.identidad.use_cases.bootstrap_administrador import BootstrapAdministradorUseCase
from src.shared.frameworks.db import SessionLocal

SALIDA_OK = 0
SALIDA_ENTRADA_INVALIDA = 1
SALIDA_SIN_PASSWORD = 2
MAX_INTENTOS_PASSWORD = 3
_YA_EXISTE = "Ya existe un Administrador operativo — no se crea otro."


class ContrasenasNoCoinciden(Exception):
    """La contraseña y su repetición no coincidieron en ninguno de los intentos permitidos."""


def pedir_password_confirmada(leer: Callable[[str], str], avisar: Callable[[str], None]) -> str:
    """Pide la contraseña y su repetición, hasta `MAX_INTENTOS_PASSWORD` veces.

    `leer` muestra el pedido y devuelve lo escrito (la terminal real le pasa `getpass.getpass`);
    `avisar` informa un desencuentro. Levanta `ContrasenasNoCoinciden` si no coinciden nunca.
    """
    for intento in range(1, MAX_INTENTOS_PASSWORD + 1):
        password = leer("Contraseña del Administrador: ")
        if password == leer("Repetí la contraseña: "):
            return password
        quedan = MAX_INTENTOS_PASSWORD - intento
        avisar(
            "Las contraseñas no coinciden."
            + (f" Te quedan {quedan} intento{'s' if quedan != 1 else ''}." if quedan else "")
        )
    raise ContrasenasNoCoinciden


def pedir_password_por_terminal() -> str | None:
    """Pide la contraseña dos veces sin eco; devuelve `None` si no hay terminal interactiva."""
    if not sys.stdin.isatty():
        return None
    return pedir_password_confirmada(getpass.getpass, print)


async def ejecutar(
    env: Mapping[str, str],
    pedir_password: Callable[[], str | None],
    repositorio: UsuarioRepositoryPort,
    hasher: PasswordHasherPort,
) -> int:
    """Orquesta el bootstrap y devuelve el código de salida del proceso."""
    faltantes = [v for v in ("ADMIN_NOMBRE", "ADMIN_EMAIL") if not env.get(v, "").strip()]
    if faltantes:
        print(f"Falta definir: {', '.join(faltantes)}.")
        return SALIDA_ENTRADA_INVALIDA

    # Con un Administrador operativo no hay nada que crear: no se pide una contraseña de más.
    if await repositorio.contar_administradores_operativos() > 0:
        print(_YA_EXISTE)
        return SALIDA_OK

    try:
        password = env.get("ADMIN_PASSWORD") or pedir_password()
    except ContrasenasNoCoinciden:
        print(
            f"Las contraseñas no coincidieron en {MAX_INTENTOS_PASSWORD} intentos: "
            "no se creó el Administrador."
        )
        return SALIDA_ENTRADA_INVALIDA
    if not password:
        print("Definí ADMIN_PASSWORD o ejecutá el comando desde una terminal interactiva.")
        return SALIDA_SIN_PASSWORD

    caso_de_uso = BootstrapAdministradorUseCase(repositorio, hasher)
    try:
        usuario = await caso_de_uso.execute(env["ADMIN_NOMBRE"], env["ADMIN_EMAIL"], password)
    except AdministradorYaExiste:  # carrera con otro proceso entre la consulta y el alta
        print(_YA_EXISTE)
        return SALIDA_OK
    except EmailYaRegistrado:
        print("Ese email ya pertenece a otra cuenta que no es un Administrador operativo.")
        return SALIDA_ENTRADA_INVALIDA
    except (PasswordDemasiadoCorta, PasswordSinComplejidadSuficiente) as error:
        print(f"Contraseña rechazada: {error}")
        return SALIDA_ENTRADA_INVALIDA

    print(f"Administrador creado: {usuario.id} ({usuario.email})")
    return SALIDA_OK


async def _main() -> int:  # pragma: no cover - cableado de infraestructura real
    async with SessionLocal() as session:
        repositorio = SQLAlchemyUsuarioRepository(session)
        return await ejecutar(
            os.environ, pedir_password_por_terminal, repositorio, BcryptPasswordHasher()
        )


def main() -> None:  # pragma: no cover - punto de entrada
    """Punto de entrada del comando."""
    raise SystemExit(asyncio.run(_main()))


if __name__ == "__main__":  # pragma: no cover
    main()
