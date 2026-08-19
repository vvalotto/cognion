from __future__ import annotations

import asyncio
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import text

from src.app import app
from src.identidad.entities.usuario import Usuario
from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher
from src.identidad.interface_adapters.gateways.usuario_repository import (
    SQLAlchemyUsuarioRepository,
)
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import SessionLocal

scenarios("../../features/inc2/US-2.2.1-bloqueo-cuenta-login.feature")

_PASSWORD_CORRECTA = "Docente#2026"


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
    run_async(_limpiar_tablas_identidad())
    yield
    run_async(_limpiar_tablas_identidad())


@pytest.fixture
def context():
    return {}


async def _post(path: str, json: dict):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(path, json=json)


async def _crear_usuario_con_estado(
    *, intentos_fallidos_login: int = 0, bloqueada: bool = False
) -> uuid.UUID:
    hasher = BcryptPasswordHasher()
    async with SessionLocal() as session:
        repo = SQLAlchemyUsuarioRepository(session)
        email = f"docente.bdd221.{uuid.uuid4()}@fiuner.edu.ar"
        usuario = Usuario.crear(
            "Docente BDD", email, hasher.hash(_PASSWORD_CORRECTA), TipoPerfil.DOCENTE
        )
        await repo.guardar(usuario)
        usuario.intentos_fallidos_login = intentos_fallidos_login
        usuario.bloqueada = bloqueada
        await repo.actualizar(usuario)
        return usuario.id


async def _obtener_usuario(usuario_id: uuid.UUID) -> Usuario:
    async with SessionLocal() as session:
        repo = SQLAlchemyUsuarioRepository(session)
        usuario = await repo.obtener_por_id(usuario_id)
        assert usuario is not None
        return usuario


@given(parsers.parse("un Usuario con intentos_fallidos_login = {n:d}"))
def usuario_con_intentos_fallidos(context, n):
    usuario_id = run_async(_crear_usuario_con_estado(intentos_fallidos_login=n))
    usuario = run_async(_obtener_usuario(usuario_id))
    context["usuario_id"] = usuario_id
    context["email"] = usuario.email


@given("un Usuario con bloqueada = true")
def usuario_bloqueado(context):
    usuario_id = run_async(_crear_usuario_con_estado(intentos_fallidos_login=3, bloqueada=True))
    usuario = run_async(_obtener_usuario(usuario_id))
    context["usuario_id"] = usuario_id
    context["email"] = usuario.email


@when("falla un intento de IniciarSesion")
def falla_intento_login(context):
    context["response"] = run_async(
        _post("/identidad/login", {"email": context["email"], "password": "incorrecta"})
    )


@when("IniciarSesion se ejecuta con credenciales correctas")
def login_con_credenciales_correctas(context):
    context["response"] = run_async(
        _post("/identidad/login", {"email": context["email"], "password": _PASSWORD_CORRECTA})
    )


@when("se ejecuta IniciarSesion con cualquier contraseña")
def login_con_cualquier_password(context):
    context["response"] = run_async(
        _post("/identidad/login", {"email": context["email"], "password": "cualquiera"})
    )


@then(parsers.parse("intentos_fallidos_login pasa a {n:d}"))
def valida_intentos_fallidos_login(context, n):
    usuario = run_async(_obtener_usuario(context["usuario_id"]))
    assert usuario.intentos_fallidos_login == n


@then("intentos_fallidos_login vuelve a 0")
def valida_intentos_fallidos_login_reseteado(context):
    usuario = run_async(_obtener_usuario(context["usuario_id"]))
    assert usuario.intentos_fallidos_login == 0


@then("intentos_fallidos_login no cambia")
def valida_intentos_fallidos_login_sin_cambios(context):
    usuario = run_async(_obtener_usuario(context["usuario_id"]))
    assert usuario.intentos_fallidos_login == 3


@then("bloqueada sigue en false")
def valida_bloqueada_false(context):
    usuario = run_async(_obtener_usuario(context["usuario_id"]))
    assert usuario.bloqueada is False


@then("bloqueada pasa a true")
def valida_bloqueada_true(context):
    usuario = run_async(_obtener_usuario(context["usuario_id"]))
    assert usuario.bloqueada is True


@then("el sistema rechaza con CredencialesInvalidas")
def valida_rechazo_credenciales_invalidas(context):
    assert context["response"].status_code == 401


@then("se emite el evento CuentaBloqueada")
def valida_evento_cuenta_bloqueada(context):
    # El evento se adjunta a la excepción `CredencialesInvalidas` dentro del use case (no hay
    # event store en el proyecto) — no es observable en el límite HTTP. Se verifica
    # explícitamente en `tests/unit/inc1/test_iniciar_sesion_use_case.py`; acá se confirma el
    # efecto observable: la cuenta queda bloqueada tras este rechazo.
    usuario = run_async(_obtener_usuario(context["usuario_id"]))
    assert usuario.bloqueada is True


@then("el sistema rechaza con CuentaBloqueadaError sin verificar la contraseña")
def valida_rechazo_cuenta_bloqueada(context):
    assert context["response"].status_code == 403
