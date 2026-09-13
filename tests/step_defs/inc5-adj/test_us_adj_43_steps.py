"""Steps BDD de US-ADJ-43 — selectores públicos de Materia/Comisión para autoregistro."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, scenarios, then, when
from sqlalchemy import text

from src.app import app
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import SessionLocal
from src.shared.frameworks.security.jwt_pyjwt import PyJWTIssuer

scenarios("../../features/inc5-adj/US-ADJ-43-pantallas-autoregistro.feature")

_PASSWORD_SEGURA = "ClaveSegura#Adj43"


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


def _headers_con_rol(rol: TipoPerfil) -> dict[str, str]:
    jwt_vo = PyJWTIssuer().emitir(uuid.uuid4(), rol)
    return {"Authorization": f"Bearer {jwt_vo.token}"}


async def _crear_materia_con_comision() -> tuple[str, str]:
    docente_headers = _headers_con_rol(TipoPerfil.DOCENTE)
    admin_headers = _headers_con_rol(TipoPerfil.ADMINISTRADOR)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        materia_resp = await client.post(
            "/materias", json={"nombre": f"Materia BDD {uuid.uuid4()}"}, headers=docente_headers
        )
        materia_id = materia_resp.json()["id"]

        admin_resp = await client.post(
            "/usuarios",
            json={
                "nombre": "Admin BDD",
                "email": f"admin.bddadj43.{uuid.uuid4()}@fiuner.edu.ar",
                "password": _PASSWORD_SEGURA,
                "perfil": "administrador",
            },
            headers=admin_headers,
        )
        admin_id = admin_resp.json()["id"]

        comision_resp = await client.post(
            "/comisiones",
            json={"materia_id": materia_id, "horario": "lu 10-12", "administrador_id": admin_id},
            headers=admin_headers,
        )
        return materia_id, comision_resp.json()["id"]


async def _crear_materia_sin_comision() -> str:
    docente_headers = _headers_con_rol(TipoPerfil.DOCENTE)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        materia_resp = await client.post(
            "/materias", json={"nombre": f"Materia BDD {uuid.uuid4()}"}, headers=docente_headers
        )
        return materia_resp.json()["id"]


async def _get(path: str) -> object:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path)


@given("que existe una Materia con al menos una Comisión activa")
def dado_materia_con_comision(context):
    materia_id, comision_id = run_async(_crear_materia_con_comision())
    context["materia_id"] = materia_id
    context["comision_id"] = comision_id


@given("que existe una Materia sin ninguna Comisión")
def dado_materia_sin_comision(context):
    context["materia_id"] = run_async(_crear_materia_sin_comision())


@when("se hace GET /identidad/autoregistro/materias sin Authorization")
def cuando_get_materias(context):
    context["response"] = run_async(_get("/identidad/autoregistro/materias"))


@when("se hace GET /identidad/autoregistro/materias/{materia_id}/comisiones sin Authorization")
def cuando_get_comisiones_de_materia(context):
    context["response"] = run_async(
        _get(f"/identidad/autoregistro/materias/{context['materia_id']}/comisiones")
    )


@when(
    "se hace GET /identidad/autoregistro/materias/{materia_id}/comisiones con un id que no existe"
)
def cuando_get_comisiones_de_materia_inexistente(context):
    context["response"] = run_async(
        _get(f"/identidad/autoregistro/materias/{uuid.uuid4()}/comisiones")
    )


@then("la respuesta es 200 OK")
def entonces_respuesta_200(context):
    assert context["response"].status_code == 200


@then("la lista incluye la materia con solo los campos id y nombre")
def entonces_lista_incluye_materia(context):
    materias = context["response"].json()
    encontrada = next((m for m in materias if m["id"] == context["materia_id"]), None)
    assert encontrada is not None
    assert set(encontrada.keys()) == {"id", "nombre"}


@then("la lista incluye la comisión con solo los campos id y horario")
def entonces_lista_incluye_comision(context):
    comisiones = context["response"].json()
    assert len(comisiones) == 1
    assert comisiones[0]["id"] == context["comision_id"]
    assert set(comisiones[0].keys()) == {"id", "horario"}


@then("la lista está vacía")
def entonces_lista_vacia(context):
    assert context["response"].json() == []
