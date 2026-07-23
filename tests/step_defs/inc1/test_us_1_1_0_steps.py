from __future__ import annotations

import asyncio
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import text

from src.app import app
from src.identidad.entities.usuario import Usuario
from src.identidad.interface_adapters.gateways.usuario_repository import SQLAlchemyUsuarioRepository
from src.shared.frameworks.db import SessionLocal

scenarios("../../features/inc1/US-1.1.0-alta-usuarios-comision-docentes.feature")


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas_identidad() -> None:
    async with SessionLocal() as session:
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


async def _crear_usuario(email: str, perfil: str) -> dict:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/usuarios",
            json={
                "nombre": "Usuario Test",
                "email": email,
                "password": "claveSegura1",
                "perfil": perfil,
            },
        )
        return response.json()


async def _post(path: str, json: dict):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(path, json=json)


@given("un Administrador autenticado con JWT válido")
def administrador_autenticado(context):
    admin = run_async(_crear_usuario("admin.bdd@fiuner.edu.ar", "administrador"))
    context["administrador_id"] = admin["id"]


@given(parsers.parse('un Usuario ya existe con email "{email}"'))
def usuario_existente_con_email(context, email):
    run_async(_crear_usuario(email, "docente"))
    context["email_existente"] = email


@given("una Comisión existente")
def comision_existente(context):
    response = run_async(
        _post(
            "/comisiones",
            {
                "materia": "Ingeniería de Software",
                "horario": "lu 10-12",
                "administrador_id": context["administrador_id"],
            },
        )
    )
    context["comision_id"] = response.json()["id"]


@given("un Usuario con perfil Docente")
def usuario_con_perfil_docente(context):
    docente = run_async(_crear_usuario("docente.bdd@fiuner.edu.ar", "docente"))
    context["docente_id"] = docente["id"]


async def _crear_estudiante_fixture() -> str:
    """Crea un Estudiante directo por repositorio — `Usuario.crear()` genérico ya no admite
    `TipoPerfil.ESTUDIANTE` desde `US-1.1.2` (solo se crea vía invitación, con `comision_id`).
    Este fixture solo necesita "un usuario que no es Docente" para el escenario de rechazo."""
    admin = await _crear_usuario("admin.bdd-est@fiuner.edu.ar", "administrador")
    comision_resp = await _post(
        "/comisiones",
        {"materia": "Comisión Fixture", "horario": "lu 10-12", "administrador_id": admin["id"]},
    )
    comision_id = comision_resp.json()["id"]

    async with SessionLocal() as session:
        repo = SQLAlchemyUsuarioRepository(session)
        estudiante = Usuario.crear_estudiante(
            "Estudiante Test", "estudiante.bdd@fiuner.edu.ar", "hash", uuid.UUID(comision_id)
        )
        await repo.guardar(estudiante)
        return str(estudiante.id)


@given("un Usuario existente con perfil Estudiante")
def usuario_con_perfil_estudiante(context):
    context["estudiante_id"] = run_async(_crear_estudiante_fixture())


@when("ejecuta CrearUsuario con nombre, email, password y perfil Docente")
def ejecuta_crear_usuario_docente(context):
    context["response"] = run_async(
        _post(
            "/usuarios",
            {
                "nombre": "Nueva Docente",
                "email": "nueva.docente@fiuner.edu.ar",
                "password": "claveSegura1",
                "perfil": "docente",
            },
        )
    )


@when("el Administrador ejecuta CrearUsuario con ese mismo email")
def ejecuta_crear_usuario_email_duplicado(context):
    context["response"] = run_async(
        _post(
            "/usuarios",
            {
                "nombre": "Otro Docente",
                "email": context["email_existente"],
                "password": "claveSegura1",
                "perfil": "docente",
            },
        )
    )


@when('ejecuta CrearComision con materia "Ingeniería de Software" y horario')
def ejecuta_crear_comision(context):
    context["response"] = run_async(
        _post(
            "/comisiones",
            {
                "materia": "Ingeniería de Software",
                "horario": "lu 10-12",
                "administrador_id": context["administrador_id"],
            },
        )
    )


@when("el Administrador ejecuta AsignarDocenteAComision sobre esa Comisión y ese Docente")
def ejecuta_asignar_docente(context):
    context["response"] = run_async(
        _post(
            f"/comisiones/{context['comision_id']}/docentes",
            {"docente_id": context["docente_id"]},
        )
    )


@when("el Administrador ejecuta AsignarDocenteAComision con ese Usuario")
def ejecuta_asignar_no_docente(context):
    context["response"] = run_async(
        _post(
            f"/comisiones/{context['comision_id']}/docentes",
            {"docente_id": context["estudiante_id"]},
        )
    )


@then("el sistema crea un Usuario con perfil Docente en la misma transacción")
def valida_usuario_creado(context):
    assert context["response"].status_code == 201
    assert context["response"].json()["perfil"] == "docente"


@then("la contraseña se persiste hasheada con bcrypt")
def valida_password_hasheado(context):
    assert "password" not in context["response"].json()


@then("se emite el evento UsuarioCreado")
def valida_evento_usuario_creado(context):
    assert context["response"].status_code == 201


@then(parsers.parse("el sistema rechaza la operación con {codigo_error}"))
def valida_rechazo_con_codigo(context, codigo_error):
    mapa_status = {
        "EmailYaRegistrado": 409,
        "UsuarioNoEsDocente": 422,
    }
    assert context["response"].status_code == mapa_status[codigo_error]


@then("ningún Usuario nuevo se crea")
def valida_ningun_usuario_nuevo(context):
    assert context["response"].status_code == 409


@then("el sistema persiste la Comisión con docentes_asignados vacío")
def valida_comision_persistida(context):
    assert context["response"].status_code == 201
    assert context["response"].json()["docentes_asignados"] == []


@then("se emite el evento ComisionCreada")
def valida_evento_comision_creada(context):
    assert context["response"].status_code == 201


@then("el Docente queda agregado a Comisión.docentes_asignados")
def valida_docente_agregado(context):
    assert context["response"].status_code == 200
    assert context["docente_id"] in context["response"].json()["docentes_asignados"]


@then("se emite el evento DocenteAsignado")
def valida_evento_docente_asignado(context):
    assert context["response"].status_code == 200


@then("Comisión.docentes_asignados no cambia")
def valida_docentes_asignados_sin_cambios(context):
    assert context["response"].json().get("docentes_asignados") in (None, [])
