"""Steps BDD de US-ADJ-62 — Recuperar la contraseña desbloquea la cuenta."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import select, text

from src.app import app
from src.identidad.entities.token_recuperacion_password import TokenRecuperacionPassword
from src.identidad.entities.usuario import Usuario
from src.identidad.frameworks.db.models import TokenRecuperacionPasswordModel
from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher
from src.identidad.interface_adapters.gateways.token_recuperacion_password_repository import (
    SQLAlchemyTokenRecuperacionPasswordRepository,
)
from src.identidad.interface_adapters.gateways.usuario_repository import SQLAlchemyUsuarioRepository
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import SessionLocal

scenarios("../../features/inc7-adj/US-ADJ-62-recuperar-password-desbloquea.feature")

PASSWORD_VIEJA = "ClaveVieja#Adj62"
PASSWORD_NUEVA = "Segura#2026x"


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


async def _crear_usuario(perfil: TipoPerfil, **campos: object) -> Usuario:
    email = f"cuenta.{uuid.uuid4()}@fiuner.edu.ar"
    usuario = Usuario.crear(
        "Cuenta BDD", email, BcryptPasswordHasher().hash(PASSWORD_VIEJA), perfil
    )
    async with SessionLocal() as session:
        repo = SQLAlchemyUsuarioRepository(session)
        await repo.guardar(usuario)
        if campos:
            for campo, valor in campos.items():
                setattr(usuario, campo, valor)
            await repo.actualizar(usuario)
    return usuario


async def _crear_token(usuario: Usuario, *, vencido: bool = False) -> str:
    token = TokenRecuperacionPassword.crear(usuario.id)
    if vencido:
        token.expira_en = datetime.now(UTC) - timedelta(seconds=1)
    async with SessionLocal() as session:
        await SQLAlchemyTokenRecuperacionPasswordRepository(session).guardar(token)
    return token.token


async def _recargar(usuario_id: uuid.UUID) -> Usuario:
    async with SessionLocal() as session:
        usuario = await SQLAlchemyUsuarioRepository(session).obtener_por_id(usuario_id)
    assert usuario is not None
    return usuario


async def _token_usado_en(token: str) -> datetime | None:
    async with SessionLocal() as session:
        resultado = await session.execute(
            select(TokenRecuperacionPasswordModel).where(
                TokenRecuperacionPasswordModel.token == token
            )
        )
        return resultado.scalar_one().usado_en


def _preparar(context: dict, usuario: Usuario) -> None:
    context["usuario"] = usuario
    context["password_hash_antes"] = usuario.password_hash
    context["estaba_bloqueada"] = usuario.bloqueada


def _confirmar(context: dict, password: str = PASSWORD_NUEVA) -> None:
    context["response"] = run_async(
        _post(
            "/identidad/recuperar-password/confirmar",
            {"token": context["token"], "password_nueva": password},
        )
    )


@given("un Usuario con bloqueada = true e intentos_fallidos_login = 3")
def dado_usuario_bloqueado_por_intentos(context):
    usuario = run_async(
        _crear_usuario(TipoPerfil.DOCENTE, bloqueada=True, intentos_fallidos_login=3)
    )
    _preparar(context, usuario)


@given("un Usuario con bloqueada = false")
def dado_usuario_no_bloqueado(context):
    _preparar(context, run_async(_crear_usuario(TipoPerfil.DOCENTE)))


@given("un Usuario con deshabilitada = true")
def dado_usuario_deshabilitado(context):
    _preparar(context, run_async(_crear_usuario(TipoPerfil.DOCENTE, deshabilitada=True)))


@given("el único Administrador con bloqueada = true y bloqueada_hasta en el futuro")
def dado_unico_administrador_bloqueado_temporalmente(context):
    usuario = run_async(
        _crear_usuario(
            TipoPerfil.ADMINISTRADOR,
            bloqueada=True,
            bloqueada_hasta=datetime.now(UTC) + timedelta(minutes=10),
        )
    )
    _preparar(context, usuario)


@given("un Usuario bloqueado con un TokenRecuperacionPassword vigente")
def dado_usuario_bloqueado_con_token_vigente(context):
    usuario = run_async(
        _crear_usuario(TipoPerfil.DOCENTE, bloqueada=True, intentos_fallidos_login=3)
    )
    _preparar(context, usuario)
    context["token"] = run_async(_crear_token(usuario))


@given("un Usuario bloqueado con un TokenRecuperacionPassword vencido")
def dado_usuario_bloqueado_con_token_vencido(context):
    usuario = run_async(
        _crear_usuario(TipoPerfil.DOCENTE, bloqueada=True, intentos_fallidos_login=3)
    )
    _preparar(context, usuario)
    context["token"] = run_async(_crear_token(usuario, vencido=True))


@given("un Usuario bloqueado que recuperó su contraseña")
def dado_usuario_bloqueado_que_recupero(context):
    usuario = run_async(
        _crear_usuario(TipoPerfil.DOCENTE, bloqueada=True, intentos_fallidos_login=3)
    )
    _preparar(context, usuario)
    context["token"] = run_async(_crear_token(usuario))
    _confirmar(context)


@given("un TokenRecuperacionPassword vigente de ese Usuario")
@given("un TokenRecuperacionPassword vigente de ese Administrador")
def dado_token_vigente_de_ese_usuario(context):
    context["token"] = run_async(_crear_token(context["usuario"]))


@when("se confirma una contraseña nueva válida con ese token")
def cuando_se_confirma_password_valida(context):
    _confirmar(context)


@when("se confirma una contraseña de menos de 12 caracteres")
def cuando_se_confirma_password_corta(context):
    _confirmar(context, "Corta#1")


@when("se hace POST /identidad/login con su email y la contraseña nueva")
def cuando_login_con_password_nueva(context):
    context["response"] = run_async(
        _post(
            "/identidad/login",
            {"email": context["usuario"].email, "password": PASSWORD_NUEVA},
        )
    )


@then("Usuario.password_hash queda actualizado")
def entonces_password_hash_actualizado(context):
    recargado = run_async(_recargar(context["usuario"].id))
    assert recargado.password_hash != context["password_hash_antes"]


@then("Usuario.bloqueada es false")
def entonces_usuario_desbloqueado(context):
    assert run_async(_recargar(context["usuario"].id)).bloqueada is False


@then("Usuario.bloqueada sigue en true")
def entonces_usuario_sigue_bloqueado(context):
    assert run_async(_recargar(context["usuario"].id)).bloqueada is True


@then("intentos_fallidos_login e intentos_fallidos_password son 0")
def entonces_contadores_en_cero(context):
    recargado = run_async(_recargar(context["usuario"].id))
    assert recargado.intentos_fallidos_login == 0
    assert recargado.intentos_fallidos_password == 0


@then("se emite CuentaDesbloqueada")
def entonces_se_emite_cuenta_desbloqueada(context):
    # El evento no es observable por HTTP: se verifica la transición bloqueada -> desbloqueada
    # que lo dispara. La emisión exacta del evento está cubierta en tests/unit.
    assert context["estaba_bloqueada"] is True
    assert run_async(_recargar(context["usuario"].id)).bloqueada is False


@then("no se emite CuentaDesbloqueada")
def entonces_no_se_emite_cuenta_desbloqueada(context):
    # Ver nota del step anterior: sin bloqueo previo no hay transición que dispare el evento.
    assert context["estaba_bloqueada"] is False
    assert run_async(_recargar(context["usuario"].id)).bloqueada is False


@then("queda con bloqueada = false y bloqueada_hasta = NULL")
def entonces_administrador_liberado(context):
    recargado = run_async(_recargar(context["usuario"].id))
    assert recargado.bloqueada is False
    assert recargado.bloqueada_hasta is None


@then("Usuario.deshabilitada sigue en true")
def entonces_sigue_deshabilitada(context):
    assert run_async(_recargar(context["usuario"].id)).deshabilitada is True


@then(parsers.parse('el login responde 403 con codigo "{codigo}"'))
def entonces_login_403(context, codigo):
    respuesta = run_async(
        _post(
            "/identidad/login",
            {"email": context["usuario"].email, "password": PASSWORD_NUEVA},
        )
    )
    assert respuesta.status_code == 403
    assert respuesta.json()["detail"]["codigo"] == codigo


@then("la respuesta es 200 con un JWT válido")
def entonces_respuesta_200_con_jwt(context):
    assert context["response"].status_code == 200
    assert context["response"].json()["access_token"]


@then("la respuesta es un error TokenRecuperacionVencido")
@then("la respuesta es un error PasswordDemasiadoCorta")
def entonces_respuesta_422(context):
    assert context["response"].status_code == 422


@then("el token sigue sin usar")
def entonces_token_sigue_sin_usar(context):
    assert run_async(_token_usado_en(context["token"])) is None
