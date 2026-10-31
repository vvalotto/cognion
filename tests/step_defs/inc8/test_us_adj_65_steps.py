"""Steps BDD de US-ADJ-65 — El comando que crea el Administrador pide la contraseña dos veces.

Contra PostgreSQL real (base descartable inline). La terminal se simula con entradas guiadas; la
terminal de verdad se prueba aparte, con un pseudoterminal, en los tests de integración.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from pytest_bdd import given, scenarios, then, when
from sqlalchemy import text

from src.identidad.frameworks.cli.bootstrap_administrador import (
    ejecutar,
    pedir_password_confirmada,
)
from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher
from src.identidad.interface_adapters.gateways.usuario_repository import SQLAlchemyUsuarioRepository
from src.shared.frameworks.db import SessionLocal

scenarios("../../features/inc8/US-ADJ-65-bootstrap-confirmacion.feature")

VALIDA = "Admin#2026-ok"
OTRA = "Otra#2026-clave"
CORTA = "Ab#1"
ENV = {"ADMIN_NOMBRE": "Ada Admin", "ADMIN_EMAIL": "ada@uner.edu.ar"}


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _vaciar() -> None:
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
def limpiar_tablas():
    """Deja vacías las tablas de usuarios antes y después de cada escenario."""
    run_async(_vaciar())
    yield
    run_async(_vaciar())


@pytest.fixture
def ctx() -> dict[str, Any]:
    """Estado compartido entre los steps de un escenario."""
    return {"env": dict(ENV), "pedidos": 0, "entradas": []}


def _contar(tabla: str) -> int:
    async def consulta() -> int:
        async with SessionLocal() as session:
            return int((await session.execute(text(f"SELECT count(*) FROM {tabla}"))).scalar_one())

    return run_async(consulta())


def _ejecutar(ctx: dict[str, Any], capsys: pytest.CaptureFixture[str], pedir) -> None:
    async def correr() -> int:
        async with SessionLocal() as session:
            return await ejecutar(
                ctx["env"], pedir, SQLAlchemyUsuarioRepository(session), BcryptPasswordHasher()
            )

    ctx["codigo"] = run_async(correr())
    ctx["salida"] = capsys.readouterr().out


def _pedir_con_teclado(ctx: dict[str, Any]):
    """Una terminal simulada que teclea `ctx['entradas']` en orden y cuenta los pedidos."""

    def pedir() -> str:
        ctx["pedidos"] += 1
        pendientes = list(ctx["entradas"])

        def leer(_pedido: str) -> str:
            return pendientes.pop(0)

        return pedir_password_confirmada(leer, print)

    return pedir


def _crear_administrador_previo() -> None:
    async def crear() -> None:
        async with SessionLocal() as session:
            codigo = await ejecutar(
                {**ENV, "ADMIN_EMAIL": "previo@uner.edu.ar", "ADMIN_PASSWORD": VALIDA},
                lambda: None,
                SQLAlchemyUsuarioRepository(session),
                BcryptPasswordHasher(),
            )
            assert codigo == 0

    run_async(crear())


# ---------------------------------------------------------------- Given


@given("una instalación sin Administrador y una terminal interactiva")
def sin_administrador_con_terminal(ctx: dict[str, Any]) -> None:
    assert _contar("administrador") == 0


@given("una instalación sin Administrador y la variable ADMIN_PASSWORD definida")
def sin_administrador_con_variable(ctx: dict[str, Any]) -> None:
    ctx["env"]["ADMIN_PASSWORD"] = VALIDA


@given("una instalación sin Administrador, sin terminal interactiva y sin ADMIN_PASSWORD")
def sin_administrador_sin_terminal(ctx: dict[str, Any]) -> None:
    ctx["sin_terminal"] = True


@given("una instalación con un Administrador operativo y una terminal interactiva")
def con_administrador_y_terminal(ctx: dict[str, Any]) -> None:
    _crear_administrador_previo()
    ctx["entradas"] = [VALIDA, VALIDA]


# ---------------------------------------------------------------- When


@when("se escribe dos veces la misma contraseña válida")
def dos_veces_valida(ctx: dict[str, Any], capsys: pytest.CaptureFixture[str]) -> None:
    ctx["entradas"] = [VALIDA, VALIDA]
    _ejecutar(ctx, capsys, _pedir_con_teclado(ctx))


@when("la primera vez las dos entradas son distintas y la segunda vez iguales")
def desencuentro_y_luego_acierto(ctx: dict[str, Any], capsys: pytest.CaptureFixture[str]) -> None:
    ctx["entradas"] = [VALIDA, OTRA, VALIDA, VALIDA]
    _ejecutar(ctx, capsys, _pedir_con_teclado(ctx))


@when("las dos entradas son distintas las tres veces")
def tres_desencuentros(ctx: dict[str, Any], capsys: pytest.CaptureFixture[str]) -> None:
    ctx["entradas"] = [VALIDA, OTRA] * 3
    _ejecutar(ctx, capsys, _pedir_con_teclado(ctx))


@when("se escribe dos veces la misma contraseña corta")
def dos_veces_corta(ctx: dict[str, Any], capsys: pytest.CaptureFixture[str]) -> None:
    ctx["entradas"] = [CORTA, CORTA]
    _ejecutar(ctx, capsys, _pedir_con_teclado(ctx))


@when("se ejecuta el comando")
def ejecutar_comando(ctx: dict[str, Any], capsys: pytest.CaptureFixture[str]) -> None:
    if ctx.get("sin_terminal"):

        def pedir() -> None:
            ctx["pedidos"] += 1
            return None

        _ejecutar(ctx, capsys, pedir)
    else:
        _ejecutar(ctx, capsys, _pedir_con_teclado(ctx))


# ---------------------------------------------------------------- Then


@then("se crea el Administrador")
def se_crea_administrador() -> None:
    assert _contar("administrador") == 1


@then('se muestra "Las contraseñas no coinciden."')
def aviso_de_desencuentro(ctx: dict[str, Any]) -> None:
    assert "Las contraseñas no coinciden." in ctx["salida"]


@then("no se crea ningún usuario")
def no_se_crea_usuario() -> None:
    assert _contar("usuario") == 0


@then("se muestra un mensaje claro de que no se creó nada")
def mensaje_no_se_creo(ctx: dict[str, Any]) -> None:
    assert "no se creó el Administrador" in ctx["salida"]


@then("se muestra el mensaje de contraseña rechazada")
def mensaje_rechazada(ctx: dict[str, Any]) -> None:
    assert "Contraseña rechazada" in ctx["salida"] and CORTA not in ctx["salida"]


@then("no se pide ninguna contraseña")
def no_se_pide(ctx: dict[str, Any]) -> None:
    assert ctx["pedidos"] == 0


@then("se muestra el mensaje de siempre")
def mensaje_de_siempre(ctx: dict[str, Any]) -> None:
    assert "ADMIN_PASSWORD" in ctx["salida"] and "terminal interactiva" in ctx["salida"]


@then("se muestra que ya existe un Administrador")
def ya_existe(ctx: dict[str, Any]) -> None:
    assert "Ya existe un Administrador operativo" in ctx["salida"]
    assert _contar("administrador") == 1


@then("la salida es 0")
def salida_0(ctx: dict[str, Any]) -> None:
    assert ctx["codigo"] == 0


@then("la salida es 1")
def salida_1(ctx: dict[str, Any]) -> None:
    assert ctx["codigo"] == 1


@then("la salida es 2")
def salida_2(ctx: dict[str, Any]) -> None:
    assert ctx["codigo"] == 2
