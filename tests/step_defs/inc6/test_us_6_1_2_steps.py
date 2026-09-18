"""Steps BDD de `US-6.1.2` — Docente crea una sesión en vivo (RF-08)."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import text

from src.app import app
from src.identidad.entities.comision import Comision
from src.identidad.entities.usuario import Usuario
from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher
from src.identidad.interface_adapters.gateways.comision_repository import (
    SQLAlchemyComisionRepository,
)
from src.identidad.interface_adapters.gateways.usuario_repository import (
    SQLAlchemyUsuarioRepository,
)
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import SessionLocal
from src.shared.frameworks.security.jwt_pyjwt import PyJWTIssuer
from tests.step_defs.inc3._auth_headers import admin_headers, docente_headers

scenarios("../../features/inc6/US-6.1.2-crear-sesion-en-vivo.feature")


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM events"))
        await session.execute(text("DELETE FROM pregunta_plantilla"))
        await session.execute(text("DELETE FROM banco"))
        await session.execute(text("DELETE FROM comision_docentes"))
        await session.execute(text("DELETE FROM estudiante"))
        await session.execute(text("DELETE FROM comision"))
        await session.execute(text("DELETE FROM materia"))
        await session.execute(text("DELETE FROM administrador"))
        await session.execute(text("DELETE FROM usuario"))
        await session.commit()


@pytest.fixture(autouse=True)
def limpiar_tablas_sesion_en_vivo():
    run_async(_limpiar_tablas())
    yield
    run_async(_limpiar_tablas())


@pytest.fixture
def context():
    return {}


async def _crear_materia_con_preguntas(cantidad: int) -> str:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        creada = await client.post(
            "/materias", json={"nombre": f"Materia {uuid.uuid4()}"}, headers=admin_headers()
        )
        banco_id = creada.json()["banco_id"]
        for i in range(cantidad):
            await client.post(
                "/preguntas/verdadero-falso",
                json={
                    "banco_id": banco_id,
                    "texto": f"Pregunta {i}",
                    "respuesta_correcta": True,
                    "unidad_tematica": "Unidad 1",
                    "tema": "Tema",
                    "dificultad": "medio",
                    "importancia": "alto",
                },
                headers=docente_headers(),
            )
        return creada.json()["id"]


async def _crear_comision(materia_id: str) -> str:
    async with SessionLocal() as session:
        admin = Usuario.crear(
            "Admin",
            f"admin.{uuid.uuid4()}@fiuner.edu.ar",
            BcryptPasswordHasher().hash("x"),
            TipoPerfil.ADMINISTRADOR,
        )
        await SQLAlchemyUsuarioRepository(session).guardar(admin)
        comision = Comision.crear(uuid.UUID(materia_id), "lu 10-12", admin.id)
        await SQLAlchemyComisionRepository(session).guardar(comision)
    return str(comision.id)


async def _post_crear_sesion(comision_id: str, cantidad: int, tiempo: int, headers: dict[str, str]):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(
            "/sesiones-en-vivo",
            json={
                "comision_id": comision_id,
                "cantidad_preguntas": cantidad,
                "tiempo_limite_por_pregunta_segundos": tiempo,
            },
            headers=headers,
        )


async def _contar_sesiones() -> int:
    async with SessionLocal() as session:
        resultado = await session.execute(
            text("SELECT count(DISTINCT aggregate_id) FROM events WHERE aggregate_type = :t"),
            {"t": "ActividadEvaluativaEnVivo"},
        )
        return resultado.scalar_one()


async def _payload_primer_evento(sesion_id: str) -> dict:
    async with SessionLocal() as session:
        resultado = await session.execute(
            text(
                "SELECT payload FROM events WHERE aggregate_type = :t AND aggregate_id = :id "
                "AND sequence_number = 1"
            ),
            {"t": "ActividadEvaluativaEnVivo", "id": sesion_id},
        )
        return resultado.scalar_one()


def _dado_comision_con_preguntas(context, cantidad: int) -> None:
    materia_id = run_async(_crear_materia_con_preguntas(cantidad))
    context["comision_id"] = run_async(_crear_comision(materia_id))


@given("una Comisión existente cuya Materia tiene un Banco con preguntas activas suficientes")
def comision_con_preguntas_suficientes(context):
    _dado_comision_con_preguntas(context, 20)


@given("una Comisión con preguntas suficientes")
def comision_con_preguntas_suficientes_alias(context):
    _dado_comision_con_preguntas(context, 20)


@given(
    parsers.parse(
        "una Comisión cuya Materia tiene un Banco con solo {cantidad:d} preguntas activas"
    )
)
def comision_con_pocas_preguntas(context, cantidad):
    _dado_comision_con_preguntas(context, cantidad)


@given("un comision_id que no corresponde a ninguna Comisión")
def comision_id_inexistente(context):
    context["comision_id"] = str(uuid.uuid4())


@given("un usuario autenticado con rol Estudiante")
def usuario_estudiante(context):
    context["comision_id"] = str(uuid.uuid4())
    jwt_vo = PyJWTIssuer().emitir(uuid.uuid4(), TipoPerfil.ESTUDIANTE)
    context["headers"] = {"Authorization": f"Bearer {jwt_vo.token}"}


@when(
    parsers.parse(
        "el Docente crea una sesión en vivo con cantidad_preguntas={cantidad:d} "
        "y tiempo_limite_por_pregunta_segundos={tiempo:d}"
    )
)
def docente_crea_sesion(context, cantidad, tiempo):
    context["antes"] = run_async(_contar_sesiones())
    context["response"] = run_async(
        _post_crear_sesion(context["comision_id"], cantidad, tiempo, docente_headers())
    )


@when(
    parsers.parse("el Docente intenta crear una sesión en vivo con cantidad_preguntas={cantidad:d}")
)
def docente_intenta_crear_con_cantidad(context, cantidad):
    context["antes"] = run_async(_contar_sesiones())
    context["response"] = run_async(
        _post_crear_sesion(context["comision_id"], cantidad, 30, docente_headers())
    )


@when(
    parsers.parse(
        "el Docente intenta crear una sesión en vivo con tiempo_limite_por_pregunta_segundos="
        "{tiempo:d}"
    )
)
def docente_intenta_crear_con_tiempo(context, tiempo):
    context["antes"] = run_async(_contar_sesiones())
    context["response"] = run_async(
        _post_crear_sesion(context["comision_id"], 10, tiempo, docente_headers())
    )


@when("el Docente intenta crear una sesión en vivo")
def docente_intenta_crear(context):
    context["response"] = run_async(
        _post_crear_sesion(context["comision_id"], 10, 30, docente_headers())
    )


@when("intenta crear una sesión en vivo")
def estudiante_intenta_crear(context):
    context["response"] = run_async(
        _post_crear_sesion(context["comision_id"], 10, 30, context["headers"])
    )


@then(
    parsers.parse("la sesión queda en estado EnEspera con {cantidad:d} preguntas fijadas al azar")
)
def sesion_en_espera_con_preguntas(context, cantidad):
    body = context["response"].json()
    assert body["estado"] == "EnEspera"
    assert body["cantidad_preguntas"] == cantidad
    payload = run_async(_payload_primer_evento(body["id"]))
    assert len(payload["preguntas"]) == cantidad
    assert len({p["pregunta_id"] for p in payload["preguntas"]}) == cantidad


@then("la respuesta HTTP es 201 con el sesion_id creado")
def respuesta_201_con_sesion_id(context):
    assert context["response"].status_code == 201
    assert uuid.UUID(context["response"].json()["id"])


@then(parsers.parse("el sistema rechaza la operación con PreguntasInsuficientes ({codigo:d})"))
def rechazo_preguntas_insuficientes(context, codigo):
    assert context["response"].status_code == codigo
    assert "preguntas" in context["response"].json()["detail"]


@then(parsers.parse("el sistema rechaza la operación con TiempoLimiteInvalido ({codigo:d})"))
def rechazo_tiempo_invalido(context, codigo):
    assert context["response"].status_code == codigo
    assert "tiempo límite" in context["response"].json()["detail"]


@then(parsers.parse("el sistema rechaza la operación con ComisionNoExiste ({codigo:d})"))
def rechazo_comision_inexistente(context, codigo):
    assert context["response"].status_code == codigo


@then("no se crea ninguna sesión")
def no_se_crea_ninguna_sesion(context):
    assert run_async(_contar_sesiones()) == context["antes"]


@then(parsers.parse("el sistema responde {codigo:d}"))
def sistema_responde(context, codigo):
    assert context["response"].status_code == codigo
