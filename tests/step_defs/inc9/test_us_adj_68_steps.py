"""Steps BDD de US-ADJ-68 — El log de acceso no muestra el token de las invitaciones.

Arrancan un `uvicorn` real como subproceso y leen su salida: requieren una base descartable inline
(`DATABASE_URL`), porque las tablas se vacían antes y después de cada escenario.
"""

from __future__ import annotations

import asyncio
import secrets
import uuid
from collections.abc import Iterator
from typing import Any

import httpx
import pytest
from pytest_bdd import given, scenarios, then, when
from sqlalchemy import text

from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import SessionLocal
from src.shared.frameworks.logging_config import enmascarar_tokens
from src.shared.frameworks.security.jwt_pyjwt import PyJWTIssuer
from tests.integration.conftest import _id_desde_headers
from tests.integration.inc8._escenarios_logging import materia_y_comision
from tests.integration.inc8._servidor_real import ServidorReal

scenarios("../../features/inc9/US-ADJ-68-token-invitacion-log.feature")


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


def _headers(perfil: TipoPerfil) -> dict[str, str]:
    return {"Authorization": f"Bearer {PyJWTIssuer().emitir(uuid.uuid4(), perfil).token}"}


def _arrancar(ctx: dict[str, Any]) -> ServidorReal:
    servidor = ServidorReal(EMAIL_MODO="consola", ENTORNO="desarrollo", LOG_LEVEL="INFO")
    servidor.iniciar()
    ctx["servidor"] = servidor
    return servidor


def _comision_con_docente(ctx: dict[str, Any]) -> None:
    servidor = _arrancar(ctx)
    docente = _headers(TipoPerfil.DOCENTE)

    async def preparar() -> None:
        async with SessionLocal() as session:
            _, comision_id, _ = await materia_y_comision(
                servidor, session, _headers(TipoPerfil.ADMINISTRADOR), docente
            )
            ctx["comision_id"] = comision_id

    run_async(preparar())
    ctx["docente"] = docente


async def _generar_invitacion(ctx: dict[str, Any]) -> str:
    async with httpx.AsyncClient(base_url=ctx["servidor"].url) as client:
        creada = await client.post(
            f"/comisiones/{ctx['comision_id']}/invitaciones",
            json={"docente_id": str(_id_desde_headers(ctx["docente"]))},
            headers=ctx["docente"],
        )
    assert creada.status_code == 201
    ctx["estado_generar"] = creada.status_code
    return creada.json()["token"]


# ---------------------------------------------------------------- Given


@given("una invitación vigente de una comisión")
def invitacion_vigente(ctx: dict[str, Any]) -> None:
    """Prepara un servidor real, una comisión con su Docente y una invitación generada por la API."""
    _comision_con_docente(ctx)
    ctx["token"] = run_async(_generar_invitacion(ctx))


@given("un token de invitación que no corresponde a ninguna invitación vigente")
def token_inexistente(ctx: dict[str, Any]) -> None:
    """Prepara un servidor real y un token que no pertenece a ninguna invitación."""
    _arrancar(ctx)
    ctx["token"] = secrets.token_urlsafe(32)


@given("una comisión de un Docente")
def comision_de_un_docente(ctx: dict[str, Any]) -> None:
    """Prepara un servidor real y una comisión con su Docente."""
    _comision_con_docente(ctx)


@given(
    'un texto de log con un segmento de menos de 20 caracteres después de "/invitaciones/"',
    target_fixture="texto_corto",
)
def texto_con_segmento_corto() -> str:
    """Devuelve una línea de log con un segmento demasiado corto para ser un token."""
    return 'GET /identidad/invitaciones/corto123 HTTP/1.1" 404'


# ---------------------------------------------------------------- When


@when("el estudiante consulta la invitación por su enlace")
@when("se consulta la invitación por su enlace")
def consultar_invitacion(ctx: dict[str, Any]) -> None:
    """Consulta `GET /identidad/invitaciones/<token>` en el servidor real."""

    async def consultar() -> None:
        async with httpx.AsyncClient(base_url=ctx["servidor"].url) as client:
            ctx["respuesta"] = await client.get(f"/identidad/invitaciones/{ctx['token']}")

    run_async(consultar())


@when("el Docente genera una invitación para la comisión")
def generar_invitacion(ctx: dict[str, Any]) -> None:
    """El Docente genera una invitación por la API real."""
    ctx["token"] = run_async(_generar_invitacion(ctx))


@when("se abre el enlace de registro con el token en la consulta")
def abrir_enlace_de_registro(ctx: dict[str, Any]) -> None:
    """Abre `/registro?token=<token>` en el servidor real."""

    async def abrir() -> None:
        async with httpx.AsyncClient(base_url=ctx["servidor"].url) as client:
            await client.get(f"/registro?token={ctx['token']}")

    run_async(abrir())


@when("el filtro de logging lo procesa", target_fixture="texto_procesado")
def procesar_texto(texto_corto: str) -> str:
    """Aplica el filtro de enmascarado al texto."""
    return enmascarar_tokens(texto_corto)


# ---------------------------------------------------------------- Then


@then("el log de acceso muestra la ruta de invitaciones con el token enmascarado")
def ruta_enmascarada(ctx: dict[str, Any]) -> None:
    """La salida real del servidor muestra la ruta de invitaciones con `***`."""
    estado = ctx["respuesta"].status_code
    salida = ctx["servidor"].esperar_en_salida(
        f'GET /identidad/invitaciones/*** HTTP/1.1" {estado}'
    )
    assert f'GET /identidad/invitaciones/*** HTTP/1.1" {estado}' in salida


@then("el token completo no aparece en la salida del servidor")
def token_ausente(ctx: dict[str, Any]) -> None:
    """El token completo no aparece en la salida del servidor."""
    assert ctx["token"] not in ctx["servidor"].salida()


@then("la línea del log conserva el método GET y el código de estado de la respuesta")
def metodo_y_estado(ctx: dict[str, Any]) -> None:
    """La línea del log conserva el método y el código de estado."""
    assert ctx["respuesta"].status_code == 200
    salida = ctx["servidor"].esperar_en_salida('GET /identidad/invitaciones/*** HTTP/1.1" 200')
    assert 'GET /identidad/invitaciones/*** HTTP/1.1" 200' in salida


@then(
    'el log de acceso muestra la ruta de la comisión con su identificador y "invitaciones" sin enmascarar'
)
def ruta_de_la_comision_intacta(ctx: dict[str, Any]) -> None:
    """La ruta de la comisión se registra sin enmascarar."""
    linea = f'POST /comisiones/{ctx["comision_id"]}/invitaciones HTTP/1.1" 201'
    assert linea in ctx["servidor"].esperar_en_salida(linea)


@then('el log de acceso muestra "token=***" y el token completo no aparece')
def token_en_query_enmascarado(ctx: dict[str, Any]) -> None:
    """`/registro?token=` sigue enmascarado como en `US-ADJ-64`."""
    salida = ctx["servidor"].esperar_en_salida("GET /registro?token=***")
    assert "GET /registro?token=***" in salida
    assert ctx["token"] not in salida


@then("el texto queda igual")
def texto_igual(texto_corto: str, texto_procesado: str) -> None:
    """El texto procesado es idéntico al original."""
    assert texto_procesado == texto_corto
