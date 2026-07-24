from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import text

from src.app import app
from src.identidad.entities.usuario import TipoPerfil
from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher
from src.shared.frameworks.db import SessionLocal
from tests.step_defs.inc1._auth_headers import admin_headers

scenarios("../../features/inc1/US-1.1.4-autenticacion-jwt.feature")


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


async def _post(path: str, json: dict, headers: dict[str, str] | None = None):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(path, json=json, headers=headers)


async def _crear_usuario(email: str, perfil: str, password: str) -> dict:
    return (
        await _post(
            "/usuarios",
            {"nombre": "Usuario Test", "email": email, "password": password, "perfil": perfil},
            headers=admin_headers(),
        )
    ).json()


_PERFIL_A_TIPO = {
    "Docente": TipoPerfil.DOCENTE.value,
    "Administrador": TipoPerfil.ADMINISTRADOR.value,
    "Estudiante": TipoPerfil.ESTUDIANTE.value,
}


def _crear_usuario_con_perfil(context, perfil: str, password: str) -> None:
    email = f"{perfil.lower()}.bdd114@fiuner.edu.ar"
    if perfil == "Estudiante":
        # Estudiante no se crea vía POST /usuarios (requiere comision_id, INV-ID-05) — se
        # inserta directo con el hasher real para poder ejercitar el login end-to-end.
        run_async(_crear_estudiante_directo(email, password))
    else:
        run_async(_crear_usuario(email, _PERFIL_A_TIPO[perfil], password))
    context["email"] = email
    context["password"] = password


async def _crear_estudiante_directo(email: str, password: str) -> None:
    import uuid

    from src.identidad.entities.comision import Comision
    from src.identidad.entities.usuario import Usuario
    from src.identidad.interface_adapters.gateways.comision_repository import (
        SQLAlchemyComisionRepository,
    )
    from src.identidad.interface_adapters.gateways.usuario_repository import (
        SQLAlchemyUsuarioRepository,
    )

    hasher = BcryptPasswordHasher()
    async with SessionLocal() as session:
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        comision_repo = SQLAlchemyComisionRepository(session)
        admin = Usuario.crear(
            "Admin BDD",
            f"admin.bdd114.{uuid.uuid4()}@fiuner.edu.ar",
            hasher.hash("x"),
            TipoPerfil.ADMINISTRADOR,
        )
        await usuario_repo.guardar(admin)
        comision = Comision.crear("IS-2026-BDD114", "lu 10-12", admin.id)
        await comision_repo.guardar(comision)
        estudiante = Usuario.crear_estudiante(
            "Estudiante BDD", email, hasher.hash(password), comision.id
        )
        await usuario_repo.guardar(estudiante)


@given(parsers.parse('un Usuario con perfil {perfil} y contraseña "{password}"'))
def usuario_con_perfil_y_password(context, perfil, password):
    _crear_usuario_con_perfil(context, perfil, password)


@given(parsers.parse("un Usuario con perfil {perfil} y contraseña correcta"))
def usuario_con_perfil_y_password_correcta(context, perfil):
    _crear_usuario_con_perfil(context, perfil, "Correcta#2026")


@given("un Usuario existente")
def usuario_existente(context):
    _crear_usuario_con_perfil(context, "Docente", "Correcta#2026")


@given("ningún Usuario registrado con ese email")
def ningun_usuario_registrado(context):
    context["email"] = "no-existe.bdd114@fiuner.edu.ar"


@when(parsers.parse('ejecuta IniciarSesion(email, "{password}")'))
def ejecuta_iniciar_sesion_con_password_literal(context, password):
    context["antes_de_login"] = datetime.now(UTC)
    context["response"] = run_async(
        _post("/identidad/login", {"email": context["email"], "password": password})
    )


@when("ejecuta IniciarSesion(email, password correcta)")
def ejecuta_iniciar_sesion_password_correcta(context):
    context["antes_de_login"] = datetime.now(UTC)
    context["response"] = run_async(
        _post("/identidad/login", {"email": context["email"], "password": context["password"]})
    )


@when("ejecuta IniciarSesion(email, password incorrecta)")
def ejecuta_iniciar_sesion_password_incorrecta(context):
    context["response"] = run_async(
        _post("/identidad/login", {"email": context["email"], "password": "password-incorrecta"})
    )


@when("ejecuta IniciarSesion(email inexistente, cualquier password)")
def ejecuta_iniciar_sesion_email_inexistente(context):
    context["response"] = run_async(
        _post("/identidad/login", {"email": context["email"], "password": "cualquier-password"})
    )


@then(parsers.parse('el sistema emite un JWT con claim rol "{rol}"'))
def valida_jwt_con_rol(context, rol):
    assert context["response"].status_code == 200
    assert context["response"].json()["rol"] == rol


@then("el JWT expira 60 minutos después de la emisión")
def valida_expiracion_60_minutos(context):
    expira_en = datetime.fromisoformat(context["response"].json()["expira_en"])
    delta_minutos = (expira_en - context["antes_de_login"]).total_seconds() / 60
    assert 59.0 <= delta_minutos <= 61.0


@then("se emite el evento SesionIniciada")
def valida_evento_sesion_iniciada(context):
    assert context["response"].status_code == 200
    assert "access_token" in context["response"].json()


@then(parsers.parse("el sistema rechaza la operación con {codigo_error}"))
def valida_rechazo_con_codigo(context, codigo_error):
    mapa_status = {"CredencialesInvalidas": 401}
    assert context["response"].status_code == mapa_status[codigo_error]


@then("el mensaje no distingue si el email existe")
def valida_mensaje_generico(context):
    assert "detail" in context["response"].json()


@then("el mensaje es idéntico al del caso de contraseña incorrecta")
def valida_mensaje_identico(context):
    # El mismo `CredencialesInvalidas` genérico se usa en ambos casos — verificado también
    # a nivel de integración en test_auth_api_integration.py.
    assert context["response"].json()["detail"] == "Email o contraseña inválidos."
