"""Steps BDD de US-ADJ-59 — Una cuenta deshabilitada no puede iniciar sesión.

El escenario `@frontend` del feature (alerta en el login) se verifica con Vitest
(`Login.test.tsx`, `LoginCuentaDeshabilitadaError.test.tsx`), no acá.
"""

from __future__ import annotations

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, scenario, then, when
from sqlalchemy import select, text, update

from src.app import app
from src.identidad.frameworks.db.models import UsuarioModel
from src.shared.frameworks.db import SessionLocal
from tests.step_defs.inc1._auth_headers import admin_headers

FEATURE = "../../features/inc7-adj/US-ADJ-59-cuenta-deshabilitada-no-inicia-sesion.feature"
PASSWORD = "Docente#2026"


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


async def _post(path: str, json: dict | None = None, headers: dict[str, str] | None = None):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(path, json=json, headers=headers)


async def _crear_docente(email: str) -> str:
    respuesta = await _post(
        "/usuarios",
        {"nombre": "Docente BDD", "email": email, "password": PASSWORD, "perfil": "docente"},
        headers=admin_headers(),
    )
    return respuesta.json()["id"]


async def _fijar_estado(email: str, **valores: object) -> None:
    async with SessionLocal() as session:
        await session.execute(
            update(UsuarioModel).where(UsuarioModel.email == email).values(**valores)
        )
        await session.commit()


async def _usuario(email: str) -> UsuarioModel:
    async with SessionLocal() as session:
        resultado = await session.execute(select(UsuarioModel).where(UsuarioModel.email == email))
        return resultado.scalar_one()


def _preparar(context, email: str, **estado: object) -> None:
    context["email"] = email
    context["usuario_id"] = run_async(_crear_docente(email))
    if estado:
        run_async(_fijar_estado(email, **estado))


def _login(context, password: str) -> None:
    context["respuesta"] = run_async(
        _post("/identidad/login", {"email": context["email"], "password": password})
    )


@scenario(FEATURE, "Login con contraseña correcta sobre una cuenta deshabilitada")
def test_login_con_contrasena_correcta_sobre_cuenta_deshabilitada():
    pass


@scenario(FEATURE, "El rechazo no depende de la contraseña ni consume intentos")
def test_el_rechazo_no_depende_de_la_contrasena():
    pass


@scenario(FEATURE, "Reactivar la cuenta restituye el acceso")
def test_reactivar_la_cuenta_restituye_el_acceso():
    pass


@scenario(FEATURE, "Deshabilitada y bloqueada a la vez")
def test_deshabilitada_y_bloqueada_a_la_vez():
    pass


@scenario(FEATURE, "Una cuenta activa no cambia de comportamiento")
def test_una_cuenta_activa_no_cambia_de_comportamiento():
    pass


@scenario(FEATURE, "Una cuenta bloqueada conserva su respuesta actual")
def test_una_cuenta_bloqueada_conserva_su_respuesta_actual():
    pass


@given("un Usuario Docente con deshabilitada = true")
def dado_docente_deshabilitado(context):
    _preparar(context, "docente.deshab.bddadj59@fiuner.edu.ar", deshabilitada=True)


@given("un Usuario con deshabilitada = true e intentos_fallidos_login = 0")
def dado_deshabilitado_sin_intentos(context):
    _preparar(
        context,
        "deshab.intentos.bddadj59@fiuner.edu.ar",
        deshabilitada=True,
        intentos_fallidos_login=0,
    )


@given("un Usuario que estuvo deshabilitado y fue reactivado con activar()")
def dado_deshabilitado_y_reactivado(context):
    _preparar(context, "reactivado.bddadj59@fiuner.edu.ar", deshabilitada=True)
    respuesta = run_async(
        _post(f"/usuarios/{context['usuario_id']}/activar", headers=admin_headers())
    )
    assert respuesta.status_code == 200


@given("un Usuario con deshabilitada = true y bloqueada = true")
def dado_deshabilitado_y_bloqueado(context):
    _preparar(
        context,
        "deshab.bloq.bddadj59@fiuner.edu.ar",
        deshabilitada=True,
        bloqueada=True,
        intentos_fallidos_login=3,
    )


@given("un Usuario con deshabilitada = false y bloqueada = false")
def dado_usuario_activo(context):
    _preparar(context, "activo.bddadj59@fiuner.edu.ar")


@given("un Usuario con bloqueada = true y deshabilitada = false")
def dado_bloqueado_no_deshabilitado(context):
    _preparar(
        context, "bloqueado.bddadj59@fiuner.edu.ar", bloqueada=True, intentos_fallidos_login=3
    )


@when("se hace POST /identidad/login con su email y su contraseña correcta")
def cuando_login_correcto(context):
    _login(context, PASSWORD)


@when("se hace POST /identidad/login con una contraseña incorrecta")
def cuando_login_incorrecto(context):
    _login(context, "una-contrasena-incorrecta")


@when("se hace POST /identidad/login con su email")
def cuando_login_con_su_email(context):
    _login(context, PASSWORD)


@when("se hace POST /identidad/login")
def cuando_login_sin_mas(context):
    _login(context, PASSWORD)


@then("la respuesta es 403")
def entonces_403(context):
    assert context["respuesta"].status_code == 403


@then('el detail tiene codigo "cuenta_deshabilitada"')
def entonces_detail_codigo(context):
    assert context["respuesta"].json()["detail"]["codigo"] == "cuenta_deshabilitada"


@then("no se emite ningún JWT")
def entonces_sin_jwt(context):
    assert "access_token" not in context["respuesta"].json()


@then('la respuesta es 403 con codigo "cuenta_deshabilitada"')
def entonces_403_con_codigo(context):
    assert context["respuesta"].status_code == 403
    assert context["respuesta"].json()["detail"]["codigo"] == "cuenta_deshabilitada"


@then("intentos_fallidos_login sigue en 0")
def entonces_intentos_en_cero(context):
    assert run_async(_usuario(context["email"])).intentos_fallidos_login == 0


@then("bloqueada sigue en false")
def entonces_bloqueada_false(context):
    assert run_async(_usuario(context["email"])).bloqueada is False


@then("la respuesta es 200 con un JWT válido")
def entonces_200_con_jwt(context):
    assert context["respuesta"].status_code == 200
    assert context["respuesta"].json()["access_token"]


@then("la respuesta es 403 con el detail en texto plano de cuenta bloqueada")
def entonces_403_bloqueada_texto_plano(context):
    assert context["respuesta"].status_code == 403
    detail = context["respuesta"].json()["detail"]
    assert isinstance(detail, str)
    assert "bloqueada" in detail
