"""Steps BDD de US-ADJ-64 — Logging local: emails de consola visibles y tokens enmascarados.

Arrancan un `uvicorn` real como subproceso y leen su salida: requieren una base descartable inline.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest
from pydantic import ValidationError
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import text

from src.identidad.entities.usuario import Usuario
from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher
from src.identidad.interface_adapters.gateways.usuario_repository import SQLAlchemyUsuarioRepository
from src.settings import Settings
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import SessionLocal
from src.shared.frameworks.security.jwt_pyjwt import PyJWTIssuer
from tests.integration.inc8._escenarios_logging import intentar_websocket, materia_y_comision
from tests.integration.inc8._servidor_real import ServidorReal

scenarios("../../features/inc8/US-ADJ-64-logging-local.feature")

_BASE = {
    "database_url": "postgresql+asyncpg://u:p@localhost:5432/cognion",
    "secret_key": "x" * 40,
}


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas() -> None:
    async with SessionLocal() as session:
        for tabla in (
            "events",
            "pregunta_plantilla",
            "banco",
            "materia",
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
    """Deja la base descartable vacía antes y después de cada escenario."""
    run_async(_limpiar_tablas())
    yield
    run_async(_limpiar_tablas())


@pytest.fixture
def ctx() -> Iterator[dict[str, Any]]:
    """Estado compartido entre los steps; detiene el servidor real al terminar."""
    estado: dict[str, Any] = {}
    yield estado
    if "servidor" in estado:
        estado["servidor"].detener()


def _jwt_docente() -> tuple[dict[str, str], str]:
    jwt = PyJWTIssuer().emitir(uuid.uuid4(), TipoPerfil.DOCENTE).token
    return {"Authorization": f"Bearer {jwt}"}, jwt


def _admin_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {PyJWTIssuer().emitir(uuid.uuid4(), TipoPerfil.ADMINISTRADOR).token}"
    }


def _arrancar(ctx: dict[str, Any], **entorno: str) -> ServidorReal:
    servidor = ServidorReal(ENTORNO="desarrollo", LOG_LEVEL="INFO", **entorno)
    servidor.iniciar()
    ctx["servidor"] = servidor
    return servidor


# ---------------------------------------------------------------- Given


@given("un servidor real con EMAIL_MODO=consola y una cuenta registrada")
def servidor_consola_con_cuenta(ctx: dict[str, Any]) -> None:
    ctx["email"] = f"docente.{uuid.uuid4()}@fiuner.edu.ar"

    async def crear() -> None:
        async with SessionLocal() as session:
            await SQLAlchemyUsuarioRepository(session).guardar(
                Usuario.crear(
                    "Docente", ctx["email"], BcryptPasswordHasher().hash("x"), TipoPerfil.DOCENTE
                )
            )

    run_async(crear())
    _arrancar(ctx, EMAIL_MODO="consola")


@given("un servidor real con EMAIL_MODO=consola y una comisión con docente")
def servidor_consola_con_comision(ctx: dict[str, Any]) -> None:
    servidor = _arrancar(ctx, EMAIL_MODO="consola")
    headers, _ = _jwt_docente()

    async def preparar() -> None:
        async with SessionLocal() as session:
            _, comision_id, _ = await materia_y_comision(
                servidor, session, _admin_headers(), headers
            )
            ctx["comision_id"] = comision_id

    run_async(preparar())
    ctx["headers"] = headers


@given("un servidor real con EMAIL_MODO=consola, una comisión con un estudiante y un docente")
def servidor_consola_con_estudiante(ctx: dict[str, Any]) -> None:
    servidor = _arrancar(ctx, EMAIL_MODO="consola")
    headers, _ = _jwt_docente()

    async def preparar() -> None:
        async with SessionLocal() as session:
            materia_id, comision_id, emails = await materia_y_comision(
                servidor, session, _admin_headers(), headers, estudiantes=1
            )
            ctx.update(materia_id=materia_id, comision_id=comision_id, email_estudiante=emails[0])

    run_async(preparar())
    ctx["headers"] = headers


@given("un servidor real y un usuario con un JWT válido")
def servidor_con_jwt(ctx: dict[str, Any]) -> None:
    _arrancar(ctx, EMAIL_MODO="consola")
    _, ctx["jwt"] = _jwt_docente()


@given("un servidor real y una invitación generada")
def servidor_con_invitacion(ctx: dict[str, Any]) -> None:
    servidor = _arrancar(ctx, EMAIL_MODO="consola")
    headers, _ = _jwt_docente()

    async def preparar() -> None:
        async with SessionLocal() as session:
            _, comision_id, _ = await materia_y_comision(
                servidor, session, _admin_headers(), headers
            )
        async with httpx.AsyncClient(base_url=servidor.url) as client:
            from tests.integration.conftest import _id_desde_headers

            resp = await client.post(
                f"/comisiones/{comision_id}/invitaciones",
                json={"docente_id": str(_id_desde_headers(headers))},
                headers=headers,
            )
            ctx["token_invitacion"] = resp.json()["token"]

    run_async(preparar())


@given("un servidor real")
def servidor_real(ctx: dict[str, Any]) -> None:
    _arrancar(ctx, EMAIL_MODO="consola")


@given(parsers.parse("la variable LOG_LEVEL con el valor {valor}"))
def variable_log_level(ctx: dict[str, Any], valor: str) -> None:
    ctx["log_level"] = valor


# ---------------------------------------------------------------- When


@when("se solicita la recuperación de contraseña de esa cuenta")
def solicitar_recuperacion(ctx: dict[str, Any]) -> None:
    async def pedir() -> None:
        async with httpx.AsyncClient(base_url=ctx["servidor"].url) as client:
            resp = await client.post(
                "/identidad/recuperar-password/solicitar", json={"email": ctx["email"]}
            )
            assert resp.status_code == 202

    run_async(pedir())
    ctx["salida"] = ctx["servidor"].esperar_en_salida("/recuperar-password/")


@when("el docente genera una invitación indicando un email destinatario")
def generar_invitacion_con_email(ctx: dict[str, Any]) -> None:
    from tests.integration.conftest import _id_desde_headers

    async def generar() -> None:
        async with httpx.AsyncClient(base_url=ctx["servidor"].url) as client:
            resp = await client.post(
                f"/comisiones/{ctx['comision_id']}/invitaciones",
                json={
                    "docente_id": str(_id_desde_headers(ctx["headers"])),
                    "email_destinatario": "alumno@fiuner.edu.ar",
                },
                headers=ctx["headers"],
            )
            assert resp.status_code == 201
            ctx["token_invitacion"] = resp.json()["token"]

    run_async(generar())
    ctx["salida"] = ctx["servidor"].esperar_en_salida("alumno@fiuner.edu.ar")


@when("el docente crea una actividad para esa comisión")
def crear_actividad(ctx: dict[str, Any]) -> None:
    async def crear() -> None:
        async with httpx.AsyncClient(base_url=ctx["servidor"].url) as client:
            materias = (await client.get("/materias", headers=ctx["headers"])).json()
            banco_id = next(m["banco_id"] for m in materias if m["id"] == ctx["materia_id"])
            for i in range(3):
                await client.post(
                    "/preguntas/verdadero-falso",
                    json={
                        "banco_id": banco_id,
                        "texto": f"Pregunta {i}",
                        "respuesta_correcta": True,
                        "unidad_tematica": "U",
                        "tema": "T",
                        "dificultad": "medio",
                        "importancia": "alto",
                    },
                    headers=ctx["headers"],
                )
            apertura = datetime.now(UTC)
            resp = await client.post(
                "/actividades",
                json={
                    "materia_id": ctx["materia_id"],
                    "fecha_apertura": apertura.isoformat(),
                    "fecha_cierre": (apertura + timedelta(days=7)).isoformat(),
                    "cantidad_preguntas": 2,
                    "cantidad_intentos_permitidos": 1,
                    "titulo": "Parcial de prueba",
                    "comisiones_ids": [ctx["comision_id"]],
                },
                headers=ctx["headers"],
            )
            assert resp.status_code == 201

    run_async(crear())
    ctx["salida"] = ctx["servidor"].esperar_en_salida(ctx["email_estudiante"])


@when("ese usuario abre una conexión WebSocket con su token")
def abrir_websocket_con_jwt(ctx: dict[str, Any]) -> None:
    run_async(intentar_websocket(ctx["servidor"], str(uuid.uuid4()), ctx["jwt"]))
    ctx["salida"] = ctx["servidor"].esperar_en_salida("token=***")


@when("se pide la página de registro con el token de la invitación")
def pedir_registro(ctx: dict[str, Any]) -> None:
    async def pedir() -> None:
        async with httpx.AsyncClient(base_url=ctx["servidor"].url) as client:
            await client.get(f"/registro?token={ctx['token_invitacion']}")

    run_async(pedir())
    ctx["salida"] = ctx["servidor"].esperar_en_salida("GET /registro?token=***")


@when("se abre una conexión WebSocket con un token inválido")
def abrir_websocket_invalido(ctx: dict[str, Any]) -> None:
    ctx["token_invalido"] = "token-invalido-secreto-123"
    run_async(intentar_websocket(ctx["servidor"], str(uuid.uuid4()), ctx["token_invalido"]))
    ctx["salida"] = ctx["servidor"].esperar_en_salida("token=***")


@when("se pide el health check")
def pedir_health(ctx: dict[str, Any]) -> None:
    async def pedir() -> None:
        async with httpx.AsyncClient(base_url=ctx["servidor"].url) as client:
            await client.get("/health")

    run_async(pedir())
    ctx["salida"] = ctx["servidor"].esperar_en_salida('"GET /health HTTP/1.1" 200 OK')


@when("se carga la configuración")
def cargar_configuracion(ctx: dict[str, Any]) -> None:
    try:
        ctx["config"] = Settings(**_BASE, log_level=ctx["log_level"])
    except ValidationError as error:
        ctx["error"] = str(error)


# ---------------------------------------------------------------- Then


@then(
    'la salida del servidor contiene "Email (modo consola)", el destinatario y el link de recuperación'
)
def salida_con_email_y_link(ctx: dict[str, Any]) -> None:
    assert "Email (modo consola)" in ctx["salida"]
    assert ctx["email"] in ctx["salida"]
    assert "/recuperar-password/" in ctx["salida"]


@then("la salida del servidor contiene el token de esa invitación en el cuerpo del email")
def salida_con_token_de_invitacion(ctx: dict[str, Any]) -> None:
    assert "Email (modo consola)" in ctx["salida"]
    assert f"Token de invitación: {ctx['token_invitacion']}" in ctx["salida"]


@then("la salida del servidor contiene el aviso de apertura dirigido al estudiante")
def salida_con_aviso(ctx: dict[str, Any]) -> None:
    assert "Email (modo consola)" in ctx["salida"]
    assert ctx["email_estudiante"] in ctx["salida"]


@then('la línea de acceso contiene "token=***"')
def linea_con_token_enmascarado(ctx: dict[str, Any]) -> None:
    assert "token=***" in ctx["salida"]


@then("el JWT no aparece en ninguna parte de la salida")
def jwt_ausente(ctx: dict[str, Any]) -> None:
    assert ctx["jwt"] not in ctx["servidor"].salida()


@then("el token de la invitación no aparece en la salida")
def invitacion_ausente(ctx: dict[str, Any]) -> None:
    assert ctx["token_invitacion"] not in ctx["servidor"].salida()


@then("la línea de rechazo no contiene el valor del token")
def rechazo_sin_token(ctx: dict[str, Any]) -> None:
    assert "token=***" in ctx["salida"]
    assert ctx["token_invalido"] not in ctx["servidor"].salida()


@then("la línea de acceso mantiene el formato de uvicorn sin enmascarados")
def formato_uvicorn(ctx: dict[str, Any]) -> None:
    assert "INFO:     127.0.0.1:" in ctx["salida"]
    assert '"GET /health HTTP/1.1" 200 OK' in ctx["salida"]
    assert "***" not in ctx["salida"].split("Application startup complete")[0]


@then(parsers.parse("el resultado es {resultado}"))
def resultado_configuracion(ctx: dict[str, Any], resultado: str) -> None:
    if resultado.startswith("nivel"):
        nivel = resultado.split()[1]
        assert ctx["config"].log_level == nivel
    else:
        mensaje = ctx["error"]
        assert all(valor in mensaje for valor in ("DEBUG", "INFO", "WARNING", "ERROR"))
