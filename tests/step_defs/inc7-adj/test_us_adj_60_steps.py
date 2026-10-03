"""Steps BDD de US-ADJ-60 — Siempre existe al menos un Administrador operativo.

El escenario `@frontend` del feature (aviso de baja de un Administrador) se verifica con Vitest
(`EliminarCuenta.test.tsx`), no acá.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, scenario, then, when
from sqlalchemy import select, text, update

from src.app import app
from src.identidad.frameworks.db.models import UsuarioModel
from src.shared.frameworks.db import SessionLocal
from tests.step_defs.inc1._auth_headers import admin_headers

FEATURE = "../../features/inc7-adj/US-ADJ-60-siempre-un-administrador-operativo.feature"
PASSWORD = "Admin#2026-ok"


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas_identidad() -> None:
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
def limpiar_tablas_identidad():
    run_async(_limpiar_tablas_identidad())
    yield
    run_async(_limpiar_tablas_identidad())


@pytest.fixture
def context():
    return {}


async def _request(metodo: str, path: str, json=None, headers=None):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.request(metodo, path, json=json, headers=headers)


async def _crear(perfil: str) -> tuple[str, str]:
    email = f"{perfil}.{uuid.uuid4().hex[:8]}.bddadj60@fiuner.edu.ar"
    respuesta = await _request(
        "POST",
        "/usuarios",
        {"nombre": "Cuenta BDD", "email": email, "password": PASSWORD, "perfil": perfil},
        headers=admin_headers(),
    )
    return respuesta.json()["id"], email


async def _fijar(email: str, **valores: object) -> None:
    async with SessionLocal() as session:
        await session.execute(
            update(UsuarioModel).where(UsuarioModel.email == email).values(**valores)
        )
        await session.commit()


async def _usuario(email: str) -> UsuarioModel:
    async with SessionLocal() as session:
        resultado = await session.execute(select(UsuarioModel).where(UsuarioModel.email == email))
        return resultado.scalar_one()


def _admin(context, clave: str = "A", **estado: object) -> None:
    usuario_id, email = run_async(_crear("administrador"))
    context[clave] = {"id": usuario_id, "email": email}
    if estado:
        run_async(_fijar(email, **estado))


def _login(context, clave: str, password: str) -> None:
    context["respuesta"] = run_async(
        _request(
            "POST", "/identidad/login", {"email": context[clave]["email"], "password": password}
        )
    )


def _fallar_login(context, clave: str, veces: int) -> None:
    for _ in range(veces):
        _login(context, clave, "incorrecta")


def _delete(context, clave: str) -> None:
    context["respuesta"] = run_async(
        _request("DELETE", f"/usuarios/{context[clave]['id']}", headers=admin_headers())
    )


@scenario(FEATURE, "Dar de baja a un Administrador sin Comisiones es siempre baja lógica")
def test_baja_logica_siempre():
    pass


@scenario(FEATURE, "No se puede dar de baja al último Administrador operativo")
def test_no_se_da_de_baja_al_ultimo():
    pass


@scenario(FEATURE, "Un Administrador bloqueado no cuenta como operativo")
def test_bloqueado_no_cuenta():
    pass


@scenario(FEATURE, "Dar de baja a un Administrador ya deshabilitado es idempotente")
def test_baja_idempotente():
    pass


@scenario(FEATURE, "Tres logins fallidos del último Administrador lo bloquean solo por un tiempo")
def test_login_bloqueo_temporal():
    pass


@scenario(FEATURE, "El bloqueo temporal se levanta solo al vencer")
def test_bloqueo_temporal_vence():
    pass


@scenario(FEATURE, "Habiendo otro Administrador operativo el bloqueo sigue siendo permanente")
def test_bloqueo_permanente_con_otro():
    pass


@scenario(
    FEATURE,
    "Tres fallos al cambiar la propia contraseña también son temporales para el último",
)
def test_cambio_password_temporal():
    pass


@scenario(FEATURE, "Docente y Estudiante conservan el bloqueo permanente")
def test_docente_permanente():
    pass


@scenario(FEATURE, "Un reseteo de contraseña limpia el bloqueo temporal")
def test_reseteo_limpia_bloqueo():
    pass


# --- Given ---


@given("dos Administradores operativos A y B, y A no creó ninguna Comisión")
@given("dos Administradores operativos A y B")
def dado_dos_administradores(context):
    _admin(context, "A")
    _admin(context, "B")


@given("un único Administrador operativo A")
def dado_unico_administrador(context):
    _admin(context, "A")


@given("un Administrador A operativo y un Administrador B con bloqueada = true")
def dado_a_operativo_b_bloqueado(context):
    _admin(context, "A")
    _admin(context, "B", bloqueada=True)


@given("un Administrador A deshabilitado y un Administrador B operativo")
def dado_a_deshabilitado_b_operativo(context):
    _admin(context, "A", deshabilitada=True)
    _admin(context, "B")


@given("A bloqueado temporalmente con bloqueada_hasta ya vencida")
def dado_bloqueo_vencido(context):
    _admin(
        context,
        "A",
        bloqueada=True,
        intentos_fallidos_login=3,
        bloqueada_hasta=datetime.now(UTC) - timedelta(seconds=5),
    )


@given("A bloqueado temporalmente")
def dado_bloqueo_vigente(context):
    _admin(
        context,
        "A",
        bloqueada=True,
        bloqueada_hasta=datetime.now(UTC) + timedelta(minutes=10),
    )
    _admin(context, "B")


@given("un único Administrador operativo A autenticado")
def dado_unico_autenticado(context):
    _admin(context, "A")
    _login(context, "A", PASSWORD)
    context["token"] = context["respuesta"].json()["access_token"]


@given("un Docente operativo")
def dado_docente(context):
    usuario_id, email = run_async(_crear("docente"))
    context["A"] = {"id": usuario_id, "email": email}


# --- When ---


@when("un Administrador da de baja a A")
@when("se hace DELETE /usuarios/{A}")
def cuando_delete_a(context):
    _delete(context, "A")


@when("se hacen 3 POST /identidad/login con una contraseña incorrecta")
@when("A falla 3 veces el login")
@when("falla 3 veces el login")
def cuando_tres_fallos_login(context):
    _fallar_login(context, "A", 3)
    context["ultima_fallida"] = context["respuesta"]


@when("A hace login con su contraseña correcta")
def cuando_login_correcto(context):
    _login(context, "A", PASSWORD)


@when("A envía 3 veces PUT /usuarios/me/password con una contraseña actual incorrecta")
def cuando_tres_fallos_cambio(context):
    headers = {"Authorization": f"Bearer {context['token']}"}
    cuerpo = {"password_actual": "incorrecta", "password_nueva": "Nueva#Pass2026"}
    for _ in range(3):
        run_async(_request("PUT", "/usuarios/me/password", cuerpo, headers))


@when("otro Administrador resetea su contraseña")
def cuando_resetea(context):
    context["respuesta"] = run_async(
        _request(
            "POST",
            f"/usuarios/{context['A']['id']}/resetear-password",
            {"password_nueva": "Reseteada#2026"},
            admin_headers(),
        )
    )


# --- Then ---


@then("la respuesta es 200 con el detalle de A")
def entonces_200_detalle(context):
    assert context["respuesta"].status_code == 200
    assert context["respuesta"].json()["id"] == context["A"]["id"]


@then("la respuesta es 200")
def entonces_200(context):
    assert context["respuesta"].status_code == 200


@then("A sigue existiendo en la tabla usuario con deshabilitada = true")
def entonces_a_existe_deshabilitada(context):
    assert run_async(_usuario(context["A"]["email"])).deshabilitada is True


@then('la respuesta es 409 con codigo "ultimo_administrador_operativo"')
def entonces_409(context):
    assert context["respuesta"].status_code == 409
    assert context["respuesta"].json()["detail"]["codigo"] == "ultimo_administrador_operativo"


@then("A sigue con deshabilitada = false")
def entonces_a_no_deshabilitada(context):
    assert run_async(_usuario(context["A"]["email"])).deshabilitada is False


@then("B sigue operativo")
def entonces_b_operativo(context):
    b = run_async(_usuario(context["B"]["email"]))
    assert b.deshabilitada is False and b.bloqueada is False


@then("A queda con bloqueada = true y bloqueada_hasta = ahora + 15 minutos")
def entonces_bloqueo_temporal(context):
    a = run_async(_usuario(context["A"]["email"]))
    assert a.bloqueada is True
    assert a.bloqueada_hasta is not None
    restante = a.bloqueada_hasta - datetime.now(UTC)
    assert timedelta(minutes=14) < restante <= timedelta(minutes=15)


@then('el siguiente login responde 403 con codigo "cuenta_bloqueada_temporal"')
def entonces_siguiente_login_temporal(context):
    _login(context, "A", PASSWORD)
    assert context["respuesta"].status_code == 403
    assert context["respuesta"].json()["detail"]["codigo"] == "cuenta_bloqueada_temporal"


@then("el detail trae reintentar_en_segundos mayor que 0")
def entonces_reintentar(context):
    assert context["respuesta"].json()["detail"]["reintentar_en_segundos"] > 0


@then("la respuesta es 200 con un JWT válido")
def entonces_200_jwt(context):
    assert context["respuesta"].status_code == 200
    assert context["respuesta"].json()["access_token"]


@then("A queda con bloqueada = false y bloqueada_hasta = NULL")
def entonces_desbloqueada(context):
    a = run_async(_usuario(context["A"]["email"]))
    assert a.bloqueada is False
    assert a.bloqueada_hasta is None


@then("A queda con bloqueada = true y bloqueada_hasta = NULL")
@then("queda con bloqueada = true y bloqueada_hasta = NULL")
def entonces_bloqueo_permanente(context):
    a = run_async(_usuario(context["A"]["email"]))
    assert a.bloqueada is True
    assert a.bloqueada_hasta is None


@then("el detail del 403 es el texto plano de cuenta bloqueada")
def entonces_detail_texto_plano(context):
    _login(context, "A", PASSWORD)
    assert context["respuesta"].status_code == 403
    assert isinstance(context["respuesta"].json()["detail"], str)
