"""`bootstrap_administrador` bajo una terminal real contra PostgreSQL (US-ADJ-65).

Requiere una base descartable (`DATABASE_URL` inline): estos tests vacían tablas de Identidad.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher
from src.shared.frameworks.db import SessionLocal
from tests.integration.inc8._terminal_simulada import TerminalSimulada

MODULO = "src.identidad.frameworks.cli.bootstrap_administrador"
EMAIL = "ada@uner.edu.ar"
ENTORNO = {"ADMIN_NOMBRE": "Ada Admin", "ADMIN_EMAIL": EMAIL, "ENTORNO": "desarrollo"}
VALIDA = "Admin#2026-ok"
OTRA = "Otra#2026-clave"


async def _vaciar_usuarios() -> None:
    async with SessionLocal() as session:
        for tabla in (
            "token_recuperacion_password",
            "invitacion",
            "comision_docentes",
            "estudiante",
            "comision",
            "docente",
            "administrador",
            "usuario",
        ):
            await session.execute(text(f"DELETE FROM {tabla}"))
        await session.commit()


@pytest.fixture(autouse=True)
async def base_limpia():
    """Deja vacías las tablas de usuarios antes y después de cada test."""
    await _vaciar_usuarios()
    yield
    await _vaciar_usuarios()


async def _usuarios() -> list[tuple[str, str]]:
    async with SessionLocal() as session:
        filas = await session.execute(text("SELECT email, password_hash FROM usuario"))
        return [(f[0], f[1]) for f in filas]


async def test_pide_la_contraseña_dos_veces_y_el_administrador_puede_iniciar_sesion() -> None:
    """Escenario 1: `getpass` real, dos pedidos, Administrador creado con esa contraseña."""
    terminal = TerminalSimulada(MODULO, ENTORNO)
    assert terminal.esperar("Contraseña del Administrador:"), terminal.salida
    terminal.escribir(VALIDA)
    assert terminal.esperar("Repetí la contraseña:"), terminal.salida
    terminal.escribir(VALIDA)
    codigo = terminal.terminar()

    assert codigo == 0, terminal.salida
    assert "Administrador creado" in terminal.salida
    assert VALIDA not in terminal.salida  # sin eco: la contraseña no se muestra
    ((email, password_hash),) = await _usuarios()
    assert email == EMAIL
    assert BcryptPasswordHasher().verificar(VALIDA, password_hash)


async def test_un_desencuentro_avisa_y_vuelve_a_pedir() -> None:
    """Escenario 2: distinta la primera vez, igual la segunda; se crea con la segunda."""
    terminal = TerminalSimulada(MODULO, ENTORNO)
    assert terminal.esperar("Contraseña del Administrador:"), terminal.salida
    terminal.escribir(VALIDA)
    assert terminal.esperar("Repetí la contraseña:"), terminal.salida
    terminal.escribir(OTRA)
    assert terminal.esperar("Las contraseñas no coinciden. Te quedan 2 intentos."), terminal.salida
    assert terminal.esperar("Contraseña del Administrador:"), terminal.salida
    terminal.escribir(OTRA)
    assert terminal.esperar("Repetí la contraseña:"), terminal.salida
    terminal.escribir(OTRA)
    codigo = terminal.terminar()

    assert codigo == 0, terminal.salida
    assert VALIDA not in terminal.salida and OTRA not in terminal.salida
    ((_, password_hash),) = await _usuarios()
    assert BcryptPasswordHasher().verificar(OTRA, password_hash)


async def test_tres_desencuentros_terminan_con_1_y_no_crean_nada() -> None:
    """Escenario 3: tres veces distintas, salida 1, ningún usuario."""
    terminal = TerminalSimulada(MODULO, ENTORNO)
    for _ in range(3):
        assert terminal.esperar("Contraseña del Administrador:"), terminal.salida
        terminal.escribir(VALIDA)
        assert terminal.esperar("Repetí la contraseña:"), terminal.salida
        terminal.escribir(OTRA)
        assert terminal.esperar("no coinciden"), terminal.salida
    codigo = terminal.terminar()

    assert codigo == 1, terminal.salida
    assert "no se creó el Administrador" in terminal.salida
    assert await _usuarios() == []


async def test_con_un_administrador_existente_no_pide_nada() -> None:
    """Escenario 7: la segunda ejecución termina con 0 sin pedir la contraseña."""
    primera = TerminalSimulada(MODULO, ENTORNO)
    assert primera.esperar("Contraseña del Administrador:"), primera.salida
    primera.escribir(VALIDA)
    assert primera.esperar("Repetí la contraseña:"), primera.salida
    primera.escribir(VALIDA)
    assert primera.terminar() == 0

    segunda = TerminalSimulada(MODULO, {**ENTORNO, "ADMIN_EMAIL": "otra@uner.edu.ar"})
    codigo = segunda.terminar()
    assert codigo == 0, segunda.salida
    assert "Contraseña del Administrador:" not in segunda.salida
    assert "Ya existe un Administrador operativo" in segunda.salida
    assert len(await _usuarios()) == 1
