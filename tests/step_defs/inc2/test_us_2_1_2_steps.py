from __future__ import annotations

import ast
import asyncio
import uuid
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, scenarios, then, when
from sqlalchemy import text

from src.app import app
from src.banco_preguntas.entities.materia import Materia
from src.banco_preguntas.interface_adapters.gateways.materia_repository import (
    SQLAlchemyMateriaRepository,
)
from src.identidad.frameworks.db.models import ComisionModel
from src.shared.frameworks.db import SessionLocal
from tests.step_defs.inc1._auth_headers import admin_headers, docente_headers

scenarios("../../features/inc2/US-2.1.2-comision-materia-port.feature")


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM comision_docentes"))
        await session.execute(text("DELETE FROM estudiante"))
        await session.execute(text("DELETE FROM comision"))
        await session.execute(text("DELETE FROM administrador"))
        await session.execute(text("DELETE FROM usuario"))
        await session.execute(text("DELETE FROM banco"))
        await session.execute(text("DELETE FROM materia"))
        await session.commit()


@pytest.fixture(autouse=True)
def limpiar_tablas():
    run_async(_limpiar_tablas())
    yield
    run_async(_limpiar_tablas())


@pytest.fixture
def context():
    return {}


async def _post(path: str, json: dict, headers: dict[str, str] | None = None):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(path, json=json, headers=headers)


async def _crear_admin_id() -> str:
    response = await _post(
        "/usuarios",
        {
            "nombre": "Admin BDD 212",
            "email": f"admin.bdd212.{uuid.uuid4()}@fiuner.edu.ar",
            "password": "claveSegura1",
            "perfil": "administrador",
        },
        headers=admin_headers(),
    )
    return response.json()["id"]


# --- Migración de datos existentes ---------------------------------------------------


async def _simular_migracion_de_datos(nombre_materia: str) -> tuple[uuid.UUID, uuid.UUID]:
    """Reproduce el backfill de la migración `295bc74948c3` sobre datos "pre-US-2.1.2".

    Agrega temporalmente una columna `materia_legado` (equivalente al viejo `comision.materia`
    string) para simular el estado de BL-002, corre la misma consulta de backfill que usa
    `upgrade()`, y la elimina al finalizar — sin tocar el historial de Alembic.
    """
    async with SessionLocal() as session:
        materia_repo = SQLAlchemyMateriaRepository(session)
        materia = Materia.crear(nombre_materia)
        await materia_repo.guardar(materia)

        comision_id = uuid.uuid4()
        await session.execute(
            text("ALTER TABLE comision ADD COLUMN IF NOT EXISTS materia_legado VARCHAR(200)")
        )
        await session.execute(
            text(
                "INSERT INTO comision (id, materia_id, horario, administrador_id, materia_legado) "
                "VALUES (:id, :materia_id_placeholder, 'lu 10-12', "
                "(SELECT id FROM administrador LIMIT 1), :materia_legado)"
            ),
            {
                "id": comision_id,
                "materia_id_placeholder": uuid.uuid4(),
                "materia_legado": nombre_materia,
            },
        )
        await session.commit()

    return comision_id, materia.id


@given('una Comisión persistida en BL-002 con materia = "Ingeniería de Software" (string)')
def comision_pre_migracion(context):
    context["nombre_materia"] = "Ingeniería de Software"
    admin_id = run_async(_crear_admin_id())
    context["admin_id"] = admin_id


@given('una Materia con nombre "Ingeniería de Software" creada en US-2.1.1')
def materia_creada(context):
    comision_id, materia_id = run_async(_simular_migracion_de_datos(context["nombre_materia"]))
    context["comision_id"] = comision_id
    context["materia_id_esperada"] = materia_id


@when("se ejecuta la migración de datos")
def ejecuta_migracion(context):
    async def _ejecutar() -> None:
        async with SessionLocal() as session:
            await session.execute(
                text(
                    "UPDATE comision SET materia_id = materia.id "
                    "FROM materia WHERE comision.materia_legado = materia.nombre "
                    "AND comision.id = :comision_id"
                ),
                {"comision_id": context["comision_id"]},
            )
            await session.execute(text("ALTER TABLE comision DROP COLUMN materia_legado"))
            await session.commit()

    run_async(_ejecutar())


@then("la Comisión queda con materia_id apuntando a esa Materia")
def valida_materia_id_migrada(context):
    async def _verificar() -> None:
        async with SessionLocal() as session:
            modelo = await session.get(ComisionModel, context["comision_id"])
            assert modelo.materia_id == context["materia_id_esperada"]

    run_async(_verificar())


# --- Alta de comisión con materia_id válido / inválido --------------------------------


@given("un Administrador autenticado", target_fixture="admin_id")
def administrador_autenticado():
    return run_async(_crear_admin_id())


@given("una Materia existente con id <materia_id>")
def materia_existente(context):
    async def _crear() -> str:
        async with SessionLocal() as session:
            materia_repo = SQLAlchemyMateriaRepository(session)
            materia = Materia.crear(f"Materia BDD 212 {uuid.uuid4()}")
            await materia_repo.guardar(materia)
            return str(materia.id)

    context["materia_id"] = run_async(_crear())


@when("ejecuta CrearComision(materia_id=<materia_id>, horario, administrador_id)")
def ejecuta_crear_comision_valida(context, admin_id):
    context["response"] = run_async(
        _post(
            "/comisiones",
            {
                "materia_id": context["materia_id"],
                "horario": "lu 10-12",
                "administrador_id": admin_id,
            },
            headers=admin_headers(),
        )
    )


@then("el sistema valida la existencia de la Materia a través de MateriaPort")
def valida_materia_validada(context):
    assert context["response"].status_code == 201


@then("la Comisión se persiste con ese materia_id")
def valida_comision_persistida_con_materia_id(context):
    assert context["response"].json()["materia_id"] == context["materia_id"]


@when("ejecuta CrearComision(materia_id=<id inexistente>, horario, administrador_id)")
def ejecuta_crear_comision_invalida(context, admin_id):
    context["response"] = run_async(
        _post(
            "/comisiones",
            {
                "materia_id": str(uuid.uuid4()),
                "horario": "lu 10-12",
                "administrador_id": admin_id,
            },
            headers=admin_headers(),
        )
    )


@then("el sistema rechaza la operación con MateriaNoExiste")
def valida_rechazo_materia_no_existe(context):
    assert context["response"].status_code == 422


@then("no se crea ninguna Comisión")
def valida_ninguna_comision_creada(context):
    assert context["response"].status_code == 422


# --- Sin imports directos entre BCs ----------------------------------------------------


@given("el código de src/identidad/", target_fixture="modulos_identidad")
def codigo_identidad():
    raiz = Path(__file__).resolve().parents[3] / "src" / "identidad"
    return [p for p in raiz.rglob("*.py") if "__pycache__" not in p.parts]


@when("se revisan sus imports", target_fixture="imports_banco_preguntas")
def revisar_imports(modulos_identidad):
    encontrados = []
    for archivo in modulos_identidad:
        arbol = ast.parse(archivo.read_text(), filename=str(archivo))
        for nodo in ast.walk(arbol):
            modulo = None
            if isinstance(nodo, ast.ImportFrom) and nodo.module:
                modulo = nodo.module
            elif isinstance(nodo, ast.Import):
                for alias in nodo.names:
                    if alias.name.startswith("src.banco_preguntas"):
                        modulo = alias.name
            if modulo and modulo.startswith("src.banco_preguntas"):
                encontrados.append(archivo)
    return encontrados


@then("ningún módulo de src/identidad/ importa directamente src/banco_preguntas/")
def valida_sin_imports_directos(imports_banco_preguntas):
    permitido = {"materia_port_in_process.py"}
    violaciones = [f for f in imports_banco_preguntas if f.name not in permitido]
    assert violaciones == [], f"Imports directos no permitidos: {violaciones}"


@then("la única comunicación es a través de src/identidad/entities/ports/materia_port.py")
def valida_unico_punto_de_comunicacion(imports_banco_preguntas):
    assert {f.name for f in imports_banco_preguntas} == {"materia_port_in_process.py"}
