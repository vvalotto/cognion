"""Steps BDD de US-ADJ-42 — Autoregistro de Estudiante (endpoint público)."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import select, text

from src.app import app
from src.identidad.frameworks.db.models import UsuarioModel
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import SessionLocal
from src.shared.frameworks.security.jwt_pyjwt import PyJWTIssuer

scenarios("../../features/inc5-adj/US-ADJ-42-autoregistro-estudiante.feature")

_PASSWORD_SEGURA = "ClaveSegura#Adj42"


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


async def _post(path: str, json: dict, headers: dict[str, str] | None = None):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(path, json=json, headers=headers)


async def _crear_comision() -> str:
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
                "email": f"admin.bddadj42.{uuid.uuid4()}@fiuner.edu.ar",
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
        return comision_resp.json()["id"]


async def _existe_usuario(email: str) -> bool:
    async with SessionLocal() as session:
        resultado = await session.execute(select(UsuarioModel).where(UsuarioModel.email == email))
        return resultado.scalar_one_or_none() is not None


async def _contar_usuarios() -> int:
    async with SessionLocal() as session:
        resultado = await session.execute(select(UsuarioModel))
        return len(resultado.scalars().all())


@given("una Comisión existente")
def dado_una_comision_existente(context):
    context["comision_id"] = run_async(_crear_comision())


@given(parsers.parse('ningún Usuario tiene el email "{email}"'))
def dado_ningun_usuario_con_email(context, email):
    context["email"] = email
    context["usuarios_antes"] = run_async(_contar_usuarios())


@given(parsers.parse('un Usuario ya existe con el email "{email}"'))
def dado_un_usuario_ya_existe(context, email):
    context["email"] = email
    run_async(
        _post(
            "/identidad/autoregistro/estudiante",
            {
                "nombre": "Estudiante BDD",
                "email": email,
                "password": _PASSWORD_SEGURA,
                "comision_id": context["comision_id"],
            },
        )
    )
    context["usuarios_antes"] = run_async(_contar_usuarios())


@given(parsers.parse('un Estudiante se autoregistró exitosamente con el email "{email}"'))
def dado_un_estudiante_ya_autoregistrado(context, email):
    context["email"] = email
    context["comision_id"] = run_async(_crear_comision())
    respuesta = run_async(
        _post(
            "/identidad/autoregistro/estudiante",
            {
                "nombre": "Estudiante BDD",
                "email": email,
                "password": _PASSWORD_SEGURA,
                "comision_id": context["comision_id"],
            },
        )
    )
    assert respuesta.status_code == 201


@when(
    "se solicita POST /identidad/autoregistro/estudiante con datos válidos y el id de esa Comisión"
)
def cuando_se_autoregistra_con_datos_validos(context):
    context["response"] = run_async(
        _post(
            "/identidad/autoregistro/estudiante",
            {
                "nombre": "Estudiante BDD",
                "email": context["email"],
                "password": _PASSWORD_SEGURA,
                "comision_id": context["comision_id"],
            },
        )
    )


@when("se solicita POST /identidad/autoregistro/estudiante con ese mismo email")
def cuando_se_autoregistra_con_email_duplicado(context):
    context["response"] = run_async(
        _post(
            "/identidad/autoregistro/estudiante",
            {
                "nombre": "Otra",
                "email": context["email"],
                "password": "OtraClave#Segura2",
                "comision_id": context["comision_id"],
            },
        )
    )


@when("se solicita POST /identidad/autoregistro/estudiante con un comision_id que no existe")
def cuando_se_autoregistra_con_comision_inexistente(context):
    context["response"] = run_async(
        _post(
            "/identidad/autoregistro/estudiante",
            {
                "nombre": "Estudiante BDD",
                "email": context["email"],
                "password": _PASSWORD_SEGURA,
                "comision_id": str(uuid.uuid4()),
            },
        )
    )


@when("se solicita POST /identidad/autoregistro/estudiante con una contraseña débil")
def cuando_se_autoregistra_con_password_debil(context):
    context["response"] = run_async(
        _post(
            "/identidad/autoregistro/estudiante",
            {
                "nombre": "Estudiante BDD",
                "email": context["email"],
                "password": "abc123",
                "comision_id": context["comision_id"],
            },
        )
    )


@when("hace POST /identidad/login con ese email y esa contraseña")
def cuando_hace_login(context):
    context["response"] = run_async(
        _post("/identidad/login", {"email": context["email"], "password": _PASSWORD_SEGURA})
    )


@then("la respuesta es 201 Created con los datos del Usuario creado")
def entonces_respuesta_201(context):
    assert context["response"].status_code == 201
    assert context["response"].json()["email"] == context["email"]


@then("el Usuario tiene perfil Estudiante, queda asignado a esa Comisión y activo de inmediato")
def entonces_usuario_estudiante_activo(context):
    data = context["response"].json()
    assert data["tipo_perfil"] == "estudiante"
    assert run_async(_existe_usuario(context["email"])) is True


@then("la respuesta es 409 Conflict")
def entonces_respuesta_409(context):
    assert context["response"].status_code == 409


@then("la respuesta es 422 Unprocessable Content")
def entonces_respuesta_422(context):
    assert context["response"].status_code == 422


@then("no se crea ningún Usuario nuevo")
def entonces_no_se_crea_usuario_nuevo(context):
    assert run_async(_contar_usuarios()) == context["usuarios_antes"]


@then("la respuesta es 200 OK con un JWT válido")
def entonces_respuesta_200_con_jwt(context):
    assert context["response"].status_code == 200
    data = context["response"].json()
    assert data["access_token"]
    assert data["rol"] == "estudiante"
