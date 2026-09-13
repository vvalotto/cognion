"""Steps BDD de US-ADJ-41 — Autoregistro de Docente (endpoint público)."""

from __future__ import annotations

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import select, text

from src.app import app
from src.identidad.frameworks.db.models import UsuarioModel
from src.shared.frameworks.db import SessionLocal

scenarios("../../features/inc5-adj/US-ADJ-41-autoregistro-docente.feature")

_PASSWORD_SEGURA = "ClaveSegura#Adj41"


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas_identidad() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM token_recuperacion_password"))
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


async def _existe_usuario(email: str) -> bool:
    async with SessionLocal() as session:
        resultado = await session.execute(
            select(UsuarioModel).where(UsuarioModel.email == email)
        )
        return resultado.scalar_one_or_none() is not None


async def _contar_usuarios() -> int:
    async with SessionLocal() as session:
        resultado = await session.execute(select(UsuarioModel))
        return len(resultado.scalars().all())


@given(parsers.parse('ningún Usuario tiene el email "{email}"'))
def dado_ningun_usuario_con_email(context, email):
    context["email"] = email
    context["usuarios_antes"] = run_async(_contar_usuarios())


@given(parsers.parse('un Usuario ya existe con el email "{email}"'))
def dado_un_usuario_ya_existe(context, email):
    context["email"] = email
    run_async(
        _post(
            "/identidad/autoregistro/docente",
            {"nombre": "Docente BDD", "email": email, "password": _PASSWORD_SEGURA},
        )
    )
    context["usuarios_antes"] = run_async(_contar_usuarios())


@given(parsers.parse('un Docente se autoregistró exitosamente con el email "{email}"'))
def dado_un_docente_ya_autoregistrado(context, email):
    context["email"] = email
    respuesta = run_async(
        _post(
            "/identidad/autoregistro/docente",
            {"nombre": "Docente BDD", "email": email, "password": _PASSWORD_SEGURA},
        )
    )
    assert respuesta.status_code == 201


@when("se solicita POST /identidad/autoregistro/docente con datos válidos")
def cuando_se_autoregistra_con_datos_validos(context):
    context["response"] = run_async(
        _post(
            "/identidad/autoregistro/docente",
            {"nombre": "Docente BDD", "email": context["email"], "password": _PASSWORD_SEGURA},
        )
    )


@when("se solicita POST /identidad/autoregistro/docente con ese mismo email")
def cuando_se_autoregistra_con_email_duplicado(context):
    context["response"] = run_async(
        _post(
            "/identidad/autoregistro/docente",
            {"nombre": "Otro", "email": context["email"], "password": "OtraClave#Segura2"},
        )
    )


@when("se solicita POST /identidad/autoregistro/docente con una contraseña débil")
def cuando_se_autoregistra_con_password_debil(context):
    context["response"] = run_async(
        _post(
            "/identidad/autoregistro/docente",
            {"nombre": "Docente BDD", "email": context["email"], "password": "abc123"},
        )
    )


@when("hace POST /identidad/login con ese email y esa contraseña")
def cuando_hace_login(context):
    context["response"] = run_async(
        _post("/identidad/login", {"email": context["email"], "password": _PASSWORD_SEGURA})
    )


@then("la respuesta es 201 Created con los datos del Usuario creado")
def entonces_respuesta_201(context):
    assert context["response"].status_code == 201
    assert context["response"].json()["email"] == context["email"]


@then("el Usuario tiene perfil Docente y queda activo de inmediato")
def entonces_usuario_docente_activo(context):
    data = context["response"].json()
    assert data["tipo_perfil"] == "docente"
    assert run_async(_existe_usuario(context["email"])) is True


@then("la respuesta es 409 Conflict")
def entonces_respuesta_409(context):
    assert context["response"].status_code == 409


@then("la respuesta es 422 Unprocessable Content")
def entonces_respuesta_422(context):
    assert context["response"].status_code == 422


@then("no se crea ningún Usuario nuevo")
def entonces_no_se_crea_usuario_nuevo(context):
    assert run_async(_contar_usuarios()) == context["usuarios_antes"]


@then("la respuesta es 200 OK con un JWT válido")
def entonces_respuesta_200_con_jwt(context):
    assert context["response"].status_code == 200
    data = context["response"].json()
    assert data["access_token"]
    assert data["rol"] == "docente"
