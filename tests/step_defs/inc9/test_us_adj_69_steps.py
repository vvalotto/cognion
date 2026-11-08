"""Steps BDD de US-ADJ-69: el login avisa "te queda 1 intento" tras el 2.º fallo."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient, Response
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import text

from src.app import app
from src.identidad.entities.usuario import Usuario
from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher
from src.identidad.interface_adapters.gateways.usuario_repository import SQLAlchemyUsuarioRepository
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import SessionLocal

scenarios("../../features/inc9/US-ADJ-69-aviso-ultimo-intento.feature")

_PASSWORD_CORRECTA = "Docente#2026"
_INCORRECTA = "otra-contraseña"


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas_identidad() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM invitacion"))
        await session.execute(text("DELETE FROM comision_docentes"))
        await session.execute(text("DELETE FROM estudiante"))
        await session.execute(text("DELETE FROM comision"))
        await session.execute(text("DELETE FROM docente"))
        await session.execute(text("DELETE FROM administrador"))
        await session.execute(text("DELETE FROM usuario"))
        await session.commit()


@pytest.fixture(autouse=True)
def limpiar_tablas_identidad():
    """Vacía las tablas de Identidad antes y después de cada escenario."""
    run_async(_limpiar_tablas_identidad())
    yield
    run_async(_limpiar_tablas_identidad())


@pytest.fixture
def context() -> dict[str, Any]:
    """Estado compartido entre los steps de un escenario."""
    return {"respuestas": []}


async def _login(email: str, password: str) -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post("/identidad/login", json={"email": email, "password": password})


async def _crear_cuenta(tipo: TipoPerfil, intentos_fallidos: int) -> str:
    email = f"persona.bdd69.{uuid.uuid4()}@fiuner.edu.ar"
    async with SessionLocal() as session:
        repo = SQLAlchemyUsuarioRepository(session)
        usuario = Usuario.crear(
            "Persona BDD", email, BcryptPasswordHasher().hash(_PASSWORD_CORRECTA), tipo
        )
        await repo.guardar(usuario)
        usuario.intentos_fallidos_login = intentos_fallidos
        await repo.actualizar(usuario)
    return email


def _intentar(context: dict[str, Any], password: str) -> None:
    respuesta = run_async(_login(context["email"], password))
    context["response"] = respuesta
    context["respuestas"].append(respuesta)


def _intentos_restantes(respuesta: Response) -> object:
    detalle = respuesta.json()["detail"]
    return detalle.get("intentos_restantes") if isinstance(detalle, dict) else None


@given("una cuenta existente sin intentos fallidos")
def cuenta_sin_intentos(context):
    """Crea una cuenta existente sin intentos fallidos."""
    context["email"] = run_async(_crear_cuenta(TipoPerfil.DOCENTE, 0))


@given(parsers.re(r"una cuenta existente con (?P<n>\d+) intentos? fallidos?"))
def cuenta_con_intentos(context, n):
    """Crea una cuenta existente con la cantidad indicada de intentos fallidos."""
    context["email"] = run_async(_crear_cuenta(TipoPerfil.DOCENTE, int(n)))


@given("un email que no corresponde a ninguna cuenta")
def email_inexistente(context):
    """Elige un email que no pertenece a ninguna cuenta."""
    context["email"] = f"no-existe.bdd69.{uuid.uuid4()}@fiuner.edu.ar"


@given("el único Administrador operativo con 1 intento fallido")
def unico_administrador(context):
    """Crea el único Administrador operativo con 1 intento fallido."""
    context["email"] = run_async(_crear_cuenta(TipoPerfil.ADMINISTRADOR, 1))


@when("se intenta iniciar sesión con una contraseña incorrecta")
def intento_incorrecto(context):
    """Intenta iniciar sesión con una contraseña incorrecta."""
    _intentar(context, _INCORRECTA)


@when(parsers.parse("se intenta iniciar sesión {n:d} veces con ese email"))
def intentos_repetidos(context, n):
    """Repite el intento incorrecto la cantidad de veces indicada."""
    for _ in range(n):
        _intentar(context, _INCORRECTA)


@when("se inicia sesión con la contraseña correcta")
def intento_correcto(context):
    """Inicia sesión con la contraseña correcta y exige que salga bien."""
    _intentar(context, _PASSWORD_CORRECTA)
    assert context["response"].status_code == 200


@then("la respuesta es 401")
def respuesta_401(context):
    """Verifica que la última respuesta sea 401."""
    assert context["response"].status_code == 401


@then("la respuesta no informa intentos restantes")
def sin_aviso(context):
    """Verifica que la última respuesta no informe intentos restantes."""
    assert _intentos_restantes(context["response"]) is None


@then("la respuesta informa que queda 1 intento")
def con_aviso(context):
    """Verifica que la última respuesta informe 1 intento restante."""
    assert _intentos_restantes(context["response"]) == 1


@then("el siguiente intento de iniciar sesión responde 403")
def siguiente_intento_403(context):
    """Verifica que el siguiente intento responda 403 (cuenta bloqueada)."""
    assert run_async(_login(context["email"], _INCORRECTA)).status_code == 403


@then("todas las respuestas son 401 sin intentos restantes")
def todas_sin_aviso(context):
    """Verifica que las tres respuestas sean 401 sin intentos restantes."""
    respuestas = context["respuestas"]
    assert len(respuestas) == 3
    assert all(r.status_code == 401 for r in respuestas)
    assert all(_intentos_restantes(r) is None for r in respuestas)
