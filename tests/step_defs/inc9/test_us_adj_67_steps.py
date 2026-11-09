"""Steps BDD de US-ADJ-67: el Docente genera un link de invitación grupal con vencimiento corto."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import Response
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import text

from src.shared.frameworks.db import SessionLocal
from tests.integration.inc9._link_grupal_comun import (
    Escenario,
    _cliente,
    _escenario,
    _generar,
    _headers,
    _preview,
    _registrar,
    _revocar,
    _ultima,
    _vencer,
)

scenarios("../../features/inc9/US-ADJ-67-link-grupal.feature")


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
    """Vacía las tablas de Identidad antes y después de cada escenario."""
    run_async(_limpiar_tablas_identidad())
    yield
    run_async(_limpiar_tablas_identidad())


@pytest.fixture
def context() -> dict[str, Any]:
    """Estado compartido entre los steps de un escenario."""
    return {"numero": 0}


def _siguiente(context: dict[str, Any]) -> int:
    context["numero"] += 1
    return context["numero"]


async def _con_sesion(funcion, *args):
    async with SessionLocal() as session:
        return await funcion(session, *args)


def _esc(context) -> Escenario:
    return context["esc"]


def _registrar_uno(context, token: str, **kwargs) -> Response:
    return run_async(_registrar(token, _siguiente(context), **kwargs))


def _usos(context) -> int:
    return run_async(_ultima(_esc(context))).json()["usos"]


def _minutos_hasta_el_vencimiento(respuesta: Response) -> float:
    vence = datetime.fromisoformat(respuesta.json()["expira_en"])
    return (vence - datetime.now(UTC)).total_seconds() / 60


@given("una comisión con un Docente asignado")
def comision_con_docente(context):
    """Siembra una comisión con su Docente asignado."""
    context["esc"] = run_async(_con_sesion(_escenario))


@given("otro Docente que no está asignado a esa comisión")
def docente_ajeno(context):
    """Prepara los encabezados de un Docente que no pertenece a la comisión."""
    context["ajeno"] = _headers(uuid.uuid4())


@given("un link grupal vigente")
def link_vigente(context):
    """Siembra la comisión y genera un link grupal vigente."""
    context["esc"] = run_async(_con_sesion(_escenario))
    context["link"] = run_async(_generar(_esc(context))).json()


@given(parsers.re(r"un link grupal vigente con (?P<n>\d+) estudiantes? ya registrados?"))
def link_vigente_con_registrados(context, n):
    """Genera un link grupal y registra a los estudiantes indicados."""
    link_vigente(context)
    for i in range(int(n)):
        assert (
            _registrar_uno(
                context, context["link"]["token"], email=f"previo{i}@fiuner.edu.ar"
            ).status_code
            == 201
        )


@given("un link grupal que ya venció")
def link_vencido(context):
    """Genera un link grupal y fuerza su vencimiento en la base."""
    link_vigente(context)
    run_async(_con_sesion(_vencer, context["link"]["id"]))


@given("una invitación individual vigente")
def invitacion_individual(context):
    """Genera una invitación individual por el endpoint que se conserva."""
    context["esc"] = run_async(_con_sesion(_escenario))
    esc = _esc(context)

    async def generar() -> Response:
        async with _cliente() as client:
            return await client.post(
                f"/comisiones/{esc.comision_id}/invitaciones",
                json={"docente_id": str(esc.docente_id)},
                headers=esc.headers,
            )

    context["individual"] = run_async(generar()).json()


@when("el Docente genera un link grupal sin indicar la duración")
def genera_por_defecto(context):
    """Genera un link grupal sin duración explícita."""
    context["response"] = run_async(_generar(_esc(context)))


@when(parsers.parse("el Docente genera un link grupal de {minutos:d} minutos"))
def genera_con_duracion(context, minutos):
    """Genera un link grupal con la duración indicada."""
    context["response"] = run_async(_generar(_esc(context), minutos))


@when("ese otro Docente intenta generar un link grupal")
def ajeno_genera(context):
    """Un Docente ajeno intenta generar un link de la comisión."""
    esc = _esc(context)

    async def intentar() -> Response:
        async with _cliente() as client:
            return await client.post(
                f"/comisiones/{esc.comision_id}/invitaciones-grupales",
                json={},
                headers=context["ajeno"],
            )

    context["respuestas"] = [run_async(intentar())]
    context["link"] = run_async(_generar(esc)).json()


@when("ese otro Docente intenta desactivar el link")
def ajeno_desactiva(context):
    """Un Docente ajeno intenta desactivar el link de la comisión."""
    context["respuestas"].append(
        run_async(_revocar(_esc(context), context["link"]["id"], context["ajeno"]))
    )


@when(parsers.parse("{n:d} estudiantes se registran con ese link"))
def registran_varios(context, n):
    """Registra estudiantes uno tras otro con el mismo link."""
    context["respuestas"] = [_registrar_uno(context, context["link"]["token"]) for _ in range(n)]


@when(parsers.parse("{n:d} estudiantes se registran a la vez con ese link"))
def registran_a_la_vez(context, n):
    """Registra estudiantes en paralelo con el mismo link."""
    token = context["link"]["token"]

    async def todos():
        return await asyncio.gather(*[_registrar(token, i) for i in range(n)])

    context["respuestas"] = list(run_async(todos()))


@when("un estudiante consulta el link y se intenta registrar")
def consulta_y_registra(context):
    """Consulta el preview y luego intenta registrarse."""
    token = context["link"]["token"]
    context["respuestas"] = [run_async(_preview(token)), _registrar_uno(context, token)]


@when("el Docente desactiva el link")
def desactiva(context):
    """Desactiva el link grupal de la comisión."""
    context["desactivado"] = run_async(_revocar(_esc(context), context["link"]["id"]))


@when("el Docente genera otro link grupal para la misma comisión")
def genera_otro(context):
    """Genera un segundo link grupal; el primero deja de servir."""
    context["anterior"] = context["link"]
    context["link"] = run_async(_generar(_esc(context))).json()


@when("el Docente consulta la última invitación grupal y todavía no generó ninguna")
def consulta_sin_links(context):
    """Consulta la última invitación grupal de una comisión sin links."""
    context["consulta"] = run_async(_ultima(_esc(context)))


@when("el Docente genera un link grupal y lo consulta")
def genera_y_consulta(context):
    """Genera un link grupal y consulta su estado."""
    context["link"] = run_async(_generar(_esc(context))).json()
    context["consulta"] = run_async(_ultima(_esc(context)))


@when("el Docente desactiva el link y lo consulta")
def desactiva_y_consulta(context):
    """Desactiva el link y consulta su estado."""
    run_async(_revocar(_esc(context), context["link"]["id"]))
    context["consulta"] = run_async(_ultima(_esc(context)))


@when("un estudiante se registra con ella y un segundo estudiante la intenta usar")
def individual_dos_usos(context):
    """Dos estudiantes intentan usar la misma invitación individual."""
    token = context["individual"]["token"]
    context["respuestas"] = [_registrar_uno(context, token), _registrar_uno(context, token)]


@when("un estudiante se intenta registrar con una contraseña que no cumple la política")
def registra_con_password_invalida(context):
    """Intenta registrarse con una contraseña sin símbolos ni números."""
    context["response"] = _registrar_uno(
        context, context["link"]["token"], password="sinsimbolosninumeros"
    )


@when("otro estudiante se intenta registrar con el mismo email")
def registra_email_repetido(context):
    """Intenta registrarse con el email de un estudiante ya registrado."""
    context["response"] = _registrar_uno(
        context, context["link"]["token"], email="previo0@fiuner.edu.ar"
    )


@then(parsers.parse("el link se crea y vence en {minutos:d} minutos"))
def vence_en_minutos(context, minutos):
    """El link se creó (201) y vence en la duración indicada."""
    respuesta = context["response"]
    assert respuesta.status_code == 201
    assert minutos - 2 < _minutos_hasta_el_vencimiento(respuesta) <= minutos


@then("el link se crea y vence en 1 hora")
def vence_en_una_hora(context):
    """El link se creó (201) y vence en 60 minutos."""
    vence_en_minutos(context, 60)


@then("la respuesta es 422")
def respuesta_422(context):
    """La respuesta fue 422."""
    assert context["response"].status_code == 422


@then("la respuesta es 409")
def respuesta_409(context):
    """La respuesta fue 409."""
    assert context["response"].status_code == 409


@then("ambas respuestas son 403")
def ambas_403(context):
    """Generar y desactivar con un Docente ajeno dieron 403."""
    assert [r.status_code for r in context["respuestas"]] == [403, 403]


@then(parsers.parse("los {n:d} registros se crean en la comisión"))
def registros_en_la_comision(context, n):
    """Todos los registros dieron 201 y quedaron en la comisión."""
    assert [r.status_code for r in context["respuestas"]] == [201] * n
    assert all(
        r.json()["comision_id"] == str(_esc(context).comision_id) for r in context["respuestas"]
    )


@then(parsers.parse("los {n:d} registros se crean"))
def registros_creados(context, n):
    """Todos los registros dieron 201."""
    assert [r.status_code for r in context["respuestas"]] == [201] * n


@then(parsers.parse("el link informa {n:d} registrados"))
def link_informa_registrados(context, n):
    """El contador del link coincide con la cantidad de registrados."""
    assert _usos(context) == n


@then("el link informa 0 registrados y sigue sirviendo")
def link_sin_registrados(context):
    """El contador sigue en 0 y el link sigue vigente."""
    ultima = run_async(_ultima(_esc(context))).json()
    assert ultima["usos"] == 0
    assert ultima["estado"] == "vigente"


@then("el link sigue informando 1 registrado")
def link_sigue_con_uno(context):
    """El contador quedó en 1."""
    assert _usos(context) == 1


@then(parsers.parse("ambas respuestas informan {codigo}"))
def ambas_informan(context, codigo):
    """El preview y el registro informan el mismo motivo."""
    for respuesta in context["respuestas"]:
        assert respuesta.status_code == 422
        assert respuesta.json()["detail"]["codigo"] == codigo


@then("la respuesta informa password_invalida")
def informa_password_invalida(context):
    """El registro informó `password_invalida`."""
    assert context["response"].status_code == 422
    assert context["response"].json()["detail"]["codigo"] == "password_invalida"


@then(parsers.parse("los {n:d} estudiantes registrados siguen en la comisión"))
def siguen_en_la_comision(context, n):
    """Quienes ya se registraron siguen inscriptos tras desactivar el link."""
    esc = _esc(context)

    async def listar() -> Response:
        async with _cliente() as client:
            return await client.get(
                f"/comisiones/{esc.comision_id}/estudiantes", headers=esc.headers
            )

    assert len(run_async(listar()).json()) == n


@then("desactivar el link por segunda vez no falla")
def desactivar_dos_veces(context):
    """Desactivar otra vez responde 204 igual que la primera."""
    segunda = run_async(_revocar(_esc(context), context["link"]["id"]))
    assert (context["desactivado"].status_code, segunda.status_code) == (204, 204)


@then("el link anterior informa invitacion_revocada")
def anterior_revocado(context):
    """El link anterior responde `invitacion_revocada`."""
    respuesta = run_async(_preview(context["anterior"]["token"]))
    assert respuesta.json()["detail"]["codigo"] == "invitacion_revocada"


@then("el link nuevo permite registrarse")
def nuevo_permite_registrarse(context):
    """El link nuevo sirve para registrarse."""
    assert _registrar_uno(context, context["link"]["token"]).status_code == 201


@then("no hay ninguna invitación grupal")
def no_hay_ninguna(context):
    """La consulta devolvió `null`."""
    assert context["consulta"].status_code == 200
    assert context["consulta"].json() is None


@then("la consulta informa estado vigente, el token, el vencimiento y 0 registrados")
def consulta_vigente(context):
    """La consulta del link vigente trae token, vencimiento y contador en 0."""
    datos = context["consulta"].json()
    assert datos["estado"] == "vigente"
    assert datos["token"] == context["link"]["token"]
    assert datos["expira_en"]
    assert datos["usos"] == 0


@then("la consulta informa estado revocada y no devuelve el token")
def consulta_revocada(context):
    """La consulta del link desactivado no devuelve el token."""
    datos = context["consulta"].json()
    assert datos["estado"] == "revocada"
    assert datos["token"] is None


@then("el primero se registra y el segundo recibe invitacion_usada")
def individual_resultado(context):
    """La individual se usa una sola vez."""
    primero, segundo = context["respuestas"]
    assert primero.status_code == 201
    assert segundo.status_code == 422
    assert segundo.json()["detail"]["codigo"] == "invitacion_usada"


@then("la invitación individual vence a los 7 días")
def individual_siete_dias(context):
    """La invitación individual conserva su vencimiento a 7 días."""
    vence = datetime.fromisoformat(context["individual"]["expira_en"])
    assert timedelta(days=6, hours=23) < vence - datetime.now(UTC) <= timedelta(days=7)
