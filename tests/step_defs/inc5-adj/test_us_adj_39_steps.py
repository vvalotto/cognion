"""Steps BDD de US-ADJ-39 — Confirmar nueva contraseña con token de recuperación."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import select, text, update

from src.app import app
from src.identidad.frameworks.db.models import TokenRecuperacionPasswordModel, UsuarioModel
from src.shared.frameworks.db import SessionLocal
from tests.step_defs.inc1._auth_headers import admin_headers

scenarios("../../features/inc5-adj/US-ADJ-39-confirmar-recuperacion-password.feature")


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


async def _post(path: str, json: dict, headers: dict[str, str] | None = None):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(path, json=json, headers=headers)


async def _crear_usuario_docente(email: str, password: str = "ClaveVieja#Adj39") -> None:
    await _post(
        "/usuarios",
        {"nombre": "Docente BDD", "email": email, "password": password, "perfil": "docente"},
        headers=admin_headers(),
    )


async def _generar_token(email: str) -> str:
    await _post("/identidad/recuperar-password/solicitar", {"email": email})
    async with SessionLocal() as session:
        resultado = await session.execute(
            select(TokenRecuperacionPasswordModel).where(
                TokenRecuperacionPasswordModel.usado_en.is_(None)
            )
        )
        return resultado.scalar_one().token


async def _usuario_por_email(email: str) -> UsuarioModel:
    async with SessionLocal() as session:
        resultado = await session.execute(select(UsuarioModel).where(UsuarioModel.email == email))
        return resultado.scalar_one()


async def _vencer_token(token: str) -> None:
    async with SessionLocal() as session:
        await session.execute(
            update(TokenRecuperacionPasswordModel)
            .where(TokenRecuperacionPasswordModel.token == token)
            .values(expira_en=datetime.now(UTC) - timedelta(seconds=1))
        )
        await session.commit()


async def _token_usado_en(token: str) -> datetime | None:
    async with SessionLocal() as session:
        resultado = await session.execute(
            select(TokenRecuperacionPasswordModel).where(
                TokenRecuperacionPasswordModel.token == token
            )
        )
        return resultado.scalar_one().usado_en


@given("un TokenRecuperacionPassword vigente y sin usar")
def dado_token_vigente_y_sin_usar(context):
    email = "docente.vigente.bddadj39@fiuner.edu.ar"
    context["email"] = email
    run_async(_crear_usuario_docente(email))
    context["token"] = run_async(_generar_token(email))
    context["password_hash_antes"] = run_async(_usuario_por_email(email)).password_hash


@given(parsers.parse("una password_nueva que cumple INV-ID-11 ampliada"))
def dado_password_valida(context):
    context["password_nueva"] = "Segura#2026x"


@given("un TokenRecuperacionPassword ya usado")
def dado_token_ya_usado(context):
    email = "docente.usado.bddadj39@fiuner.edu.ar"
    context["email"] = email
    run_async(_crear_usuario_docente(email))
    token = run_async(_generar_token(email))
    run_async(
        _post(
            "/identidad/recuperar-password/confirmar",
            {"token": token, "password_nueva": "PrimerCanje#12"},
        )
    )
    context["token"] = token
    context["password_hash_antes"] = run_async(_usuario_por_email(email)).password_hash


@given("un TokenRecuperacionPassword cuya expira_en ya pasó")
def dado_token_vencido(context):
    email = "docente.vencido.bddadj39@fiuner.edu.ar"
    context["email"] = email
    run_async(_crear_usuario_docente(email))
    token = run_async(_generar_token(email))
    run_async(_vencer_token(token))
    context["token"] = token


@given("ningún TokenRecuperacionPassword tiene el token dado")
def dado_ningun_token_con_ese_valor(context):
    context["token"] = "token-inexistente-bddadj39"


@given(parsers.parse("una password_nueva de menos de 12 caracteres"))
def dado_password_corta(context):
    context["password_nueva"] = "Corta#1"


@given("un Usuario bloqueado con un TokenRecuperacionPassword vigente")
def dado_usuario_bloqueado_con_token_vigente(context):
    email = "docente.bloqueado.bddadj39@fiuner.edu.ar"
    context["email"] = email
    run_async(_crear_usuario_docente(email))
    for _ in range(3):
        run_async(_post("/identidad/login", {"email": email, "password": "password-incorrecta"}))
    usuario = run_async(_usuario_por_email(email))
    assert usuario.bloqueada is True
    context["password_hash_antes"] = usuario.password_hash
    context["token"] = run_async(_generar_token(email))


@when("se hace POST /identidad/recuperar-password/confirmar con ese token y esa password")
def cuando_se_confirma_con_token_y_password(context):
    context["response"] = run_async(
        _post(
            "/identidad/recuperar-password/confirmar",
            {"token": context["token"], "password_nueva": context["password_nueva"]},
        )
    )


@when("se hace POST /identidad/recuperar-password/confirmar con ese token")
def cuando_se_confirma_solo_con_token(context):
    context["response"] = run_async(
        _post(
            "/identidad/recuperar-password/confirmar",
            {"token": context["token"], "password_nueva": "Segura#2026x"},
        )
    )


@when("se confirma una contraseña nueva válida con ese token")
def cuando_se_confirma_password_valida(context):
    context["response"] = run_async(
        _post(
            "/identidad/recuperar-password/confirmar",
            {"token": context["token"], "password_nueva": "Segura#2026x"},
        )
    )


@then("la respuesta es 200 OK")
def entonces_respuesta_200(context):
    assert context["response"].status_code == 200


@then("Usuario.password_hash queda actualizado")
def entonces_password_hash_actualizado(context):
    usuario = run_async(_usuario_por_email(context["email"]))
    assert usuario.password_hash != context["password_hash_antes"]


@then("el token queda marcado como usado")
def entonces_token_marcado_como_usado(context):
    assert run_async(_token_usado_en(context["token"])) is not None


@then("la respuesta es un error TokenRecuperacionYaUsado")
def entonces_error_ya_usado(context):
    assert context["response"].status_code == 422


@then("Usuario.password_hash no cambia")
def entonces_password_hash_no_cambia(context):
    usuario = run_async(_usuario_por_email(context["email"]))
    assert usuario.password_hash == context["password_hash_antes"]


@then("la respuesta es un error TokenRecuperacionVencido")
def entonces_error_vencido(context):
    assert context["response"].status_code == 422


@then("la respuesta es un error TokenRecuperacionInvalido")
def entonces_error_invalido(context):
    assert context["response"].status_code == 422


@then("la respuesta es un error PasswordDemasiadoCorta")
def entonces_error_password_corta(context):
    assert context["response"].status_code == 422


@then("el token sigue sin usar")
def entonces_token_sigue_sin_usar(context):
    assert run_async(_token_usado_en(context["token"])) is None


@then("Usuario.bloqueada sigue en true")
def entonces_usuario_sigue_bloqueado(context):
    usuario = run_async(_usuario_por_email(context["email"]))
    assert usuario.bloqueada is True
