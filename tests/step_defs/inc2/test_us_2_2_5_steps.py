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
from src.shared.frameworks.security.jwt_pyjwt import PyJWTIssuer

scenarios("../../features/inc2/US-2.2.5-cambiar-password.feature")

_PASSWORD_ACTUAL = "claveActual1"


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


def _headers_para(usuario_id: uuid.UUID) -> dict[str, str]:
    jwt_vo = PyJWTIssuer().emitir(usuario_id, TipoPerfil.DOCENTE)
    return {"Authorization": f"Bearer {jwt_vo.token}"}


async def _crear_usuario_con_estado(*, bloqueada: bool, intentos_fallidos_password: int) -> uuid.UUID:
    hasher = BcryptPasswordHasher()
    async with SessionLocal() as session:
        repo = SQLAlchemyUsuarioRepository(session)
        email = f"docente.bdd225.{uuid.uuid4()}@fiuner.edu.ar"
        usuario = Usuario.crear(
            "Docente BDD", email, hasher.hash(_PASSWORD_ACTUAL), TipoPerfil.DOCENTE
        )
        await repo.guardar(usuario)
        usuario.bloqueada = bloqueada
        usuario.intentos_fallidos_password = intentos_fallidos_password
        await repo.actualizar(usuario)
        return usuario.id


async def _obtener_usuario(usuario_id: uuid.UUID) -> Usuario:
    async with SessionLocal() as session:
        repo = SQLAlchemyUsuarioRepository(session)
        usuario = await repo.obtener_por_id(usuario_id)
        assert usuario is not None
        return usuario


async def _put_cambiar_password(
    usuario_id: uuid.UUID, password_actual: str, password_nueva: str, context: dict
):
    token = _headers_para(usuario_id)
    context["token_usado"] = token["Authorization"].removeprefix("Bearer ")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.put(
            "/usuarios/me/password",
            json={"password_actual": password_actual, "password_nueva": password_nueva},
            headers=token,
        )


@given("un Usuario autenticado con su contraseña actual correcta")
def usuario_autenticado_con_password_correcta(context):
    usuario_id = run_async(_crear_usuario_con_estado(bloqueada=False, intentos_fallidos_password=0))
    usuario = run_async(_obtener_usuario(usuario_id))
    context["usuario_id"] = usuario_id
    context["password_hash_original"] = usuario.password_hash


@given(parsers.parse("un Usuario con intentos_fallidos_password = {intentos:d}"))
def usuario_con_intentos_fallidos(context, intentos):
    usuario_id = run_async(
        _crear_usuario_con_estado(bloqueada=False, intentos_fallidos_password=intentos)
    )
    usuario = run_async(_obtener_usuario(usuario_id))
    context["usuario_id"] = usuario_id
    context["password_hash_original"] = usuario.password_hash


@given("un Usuario con bloqueada = true")
def usuario_bloqueado(context):
    usuario_id = run_async(_crear_usuario_con_estado(bloqueada=True, intentos_fallidos_password=3))
    usuario = run_async(_obtener_usuario(usuario_id))
    context["usuario_id"] = usuario_id
    context["password_hash_original"] = usuario.password_hash


@when(parsers.parse('ejecuta CambiarPassword(usuario_id, password_actual, "{password_nueva}")'))
def ejecuta_cambiar_password_exitoso(context, password_nueva):
    context["response"] = run_async(
        _put_cambiar_password(context["usuario_id"], _PASSWORD_ACTUAL, password_nueva, context)
    )


@when("ejecuta CambiarPassword con la contraseña actual incorrecta")
def ejecuta_cambiar_password_actual_incorrecta(context):
    context["response"] = run_async(
        _put_cambiar_password(context["usuario_id"], "incorrecta", "nuevaClave123", context)
    )


@when(parsers.parse("ejecuta CambiarPassword con password_nueva de {largo:d} caracteres"))
def ejecuta_cambiar_password_nueva_corta(context, largo):
    password_nueva = "x" * largo
    context["response"] = run_async(
        _put_cambiar_password(context["usuario_id"], _PASSWORD_ACTUAL, password_nueva, context)
    )


@when("ejecuta CambiarPassword con cualquier dato")
def ejecuta_cambiar_password_cuenta_bloqueada(context):
    context["response"] = run_async(
        _put_cambiar_password(context["usuario_id"], "cualquiera", "nuevaClave123", context)
    )


@then("el sistema actualiza password_hash")
def valida_actualiza_password_hash(context):
    assert context["response"].status_code == 204
    usuario = run_async(_obtener_usuario(context["usuario_id"]))
    assert usuario.password_hash != context["password_hash_original"]


@then("intentos_fallidos_password vuelve a 0")
def valida_intentos_fallidos_password_en_cero(context):
    usuario = run_async(_obtener_usuario(context["usuario_id"]))
    assert usuario.intentos_fallidos_password == 0


@then("se emite PasswordCambiada")
def valida_evento_password_cambiada(context):
    # Sin event store en el proyecto (mismo criterio que US-2.2.1/US-2.2.4): se verifica el
    # efecto observable acá y la emisión del evento en
    # `tests/unit/inc1/test_cambiar_password_use_case.py`.
    assert context["response"].status_code == 204


@then("el JWT en curso sigue siendo válido")
def valida_jwt_en_curso_sigue_valido(context):
    # ADR-013: sin invalidación de JWT — el mismo token usado en el request PUT sigue
    # decodificando correctamente después del cambio (no hay blacklist).
    payload = PyJWTIssuer().verificar(context["token_usado"])
    assert payload.usuario_id == context["usuario_id"]


@then(parsers.parse("intentos_fallidos_password pasa a {intentos:d}"))
def valida_intentos_fallidos_password_pasa_a(context, intentos):
    usuario = run_async(_obtener_usuario(context["usuario_id"]))
    assert usuario.intentos_fallidos_password == intentos


@then("el sistema rechaza con PasswordActualIncorrecta")
def valida_rechazo_password_actual_incorrecta(context):
    assert context["response"].status_code == 401
    usuario = run_async(_obtener_usuario(context["usuario_id"]))
    assert usuario.password_hash == context["password_hash_original"]


@then("bloqueada pasa a true")
def valida_bloqueada_pasa_a_true(context):
    usuario = run_async(_obtener_usuario(context["usuario_id"]))
    assert usuario.bloqueada is True


@then("se emite CuentaBloqueada")
def valida_evento_cuenta_bloqueada(context):
    # Sin event store (mismo criterio que arriba): efecto observable ya verificado en el step
    # anterior; la emisión del evento se verifica en
    # `tests/unit/inc1/test_cambiar_password_use_case.py`.
    assert context["response"].status_code == 401


@then("el sistema rechaza con PasswordDemasiadoCorta")
def valida_rechazo_password_demasiado_corta(context):
    assert context["response"].status_code == 422
    usuario = run_async(_obtener_usuario(context["usuario_id"]))
    assert usuario.password_hash == context["password_hash_original"]


@then("el sistema rechaza con CuentaBloqueadaError sin verificar password_actual")
def valida_rechazo_cuenta_bloqueada(context):
    assert context["response"].status_code == 403
    usuario = run_async(_obtener_usuario(context["usuario_id"]))
    assert usuario.password_hash == context["password_hash_original"]
