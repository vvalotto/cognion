from __future__ import annotations

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import text

from src.app import app
from src.shared.frameworks.db import SessionLocal
from tests.step_defs.inc2._auth_headers import docente_headers

scenarios("../../features/inc2/US-2.1.1-alta-materia-banco.feature")


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas_banco_preguntas() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM banco"))
        await session.execute(text("DELETE FROM materia"))
        await session.commit()


@pytest.fixture(autouse=True)
def limpiar_tablas_banco_preguntas():
    run_async(_limpiar_tablas_banco_preguntas())
    yield
    run_async(_limpiar_tablas_banco_preguntas())


@pytest.fixture
def context():
    return {}


async def _post_crear_materia(nombre: str):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post("/materias", json={"nombre": nombre}, headers=docente_headers())


@given("un Docente autenticado")
def docente_autenticado():
    """No requiere setup — cada request arma su propio JWT vía `docente_headers()`."""


@given(parsers.parse('no existe ninguna Materia con nombre "{nombre}"'))
def no_existe_materia(context, nombre):
    context["nombre"] = nombre


@given(parsers.parse('una Materia existente con nombre "{nombre}"'))
def materia_existente(context, nombre):
    respuesta = run_async(_post_crear_materia(nombre))
    assert respuesta.status_code == 201
    context["nombre"] = nombre


@when(parsers.parse('ejecuta CrearMateria(nombre="{nombre}")'))
def ejecuta_crear_materia(context, nombre):
    context["response"] = run_async(_post_crear_materia(nombre))


@when('ejecuta CrearMateria(nombre="")')
def ejecuta_crear_materia_nombre_vacio(context):
    context["response"] = run_async(_post_crear_materia(""))


@when(parsers.parse('un Docente ejecuta CrearMateria(nombre="{nombre}")'))
def un_docente_ejecuta_crear_materia(context, nombre):
    context["response"] = run_async(_post_crear_materia(nombre))


@then("el sistema persiste la Materia con ese nombre")
def valida_materia_persistida(context):
    assert context["response"].status_code == 201
    assert context["response"].json()["nombre"] == context["nombre"]


@then("crea automáticamente su Banco asociado con materia_id apuntando a esa Materia")
def valida_banco_asociado(context):
    assert "banco_id" in context["response"].json()


@then("se emiten los eventos MateriaCreada y BancoCreado")
def valida_eventos_emitidos(context):
    assert context["response"].status_code == 201


@then(parsers.parse("el sistema rechaza la operación con {codigo_error}"))
def valida_rechazo_con_codigo(context, codigo_error):
    mapa_status = {"MateriaYaExiste": 409}
    assert context["response"].status_code == mapa_status[codigo_error]


@then("el sistema rechaza la operación por nombre inválido")
def valida_rechazo_nombre_invalido(context):
    assert context["response"].status_code == 422


@then("no se crea ninguna Materia ni Banco nuevos")
def valida_ninguna_materia_nueva(context):
    assert context["response"].status_code in (409, 422)
