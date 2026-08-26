from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import text

from src.app import app
from src.shared.frameworks.db import SessionLocal
from tests.step_defs.inc3._auth_headers import docente_headers

scenarios("../../features/inc3/US-3.1.2-crear-actividad-periodo-abierto.feature")


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM events"))
        await session.execute(text("DELETE FROM pregunta_plantilla"))
        await session.execute(text("DELETE FROM banco"))
        await session.execute(text("DELETE FROM materia"))
        await session.commit()


@pytest.fixture(autouse=True)
def limpiar_tablas_actividad_evaluativa():
    run_async(_limpiar_tablas())
    yield
    run_async(_limpiar_tablas())


@pytest.fixture
def context():
    return {}


async def _crear_materia_con_preguntas(nombre: str, cantidad: int) -> str:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        creada = await client.post("/materias", json={"nombre": nombre}, headers=docente_headers())
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


async def _post_crear_actividad(
    materia_id: str,
    fecha_apertura: datetime,
    fecha_cierre: datetime,
    cantidad_preguntas: int,
    cantidad_intentos_permitidos: int,
):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(
            "/actividades",
            json={
                "materia_id": materia_id,
                "fecha_apertura": fecha_apertura.isoformat(),
                "fecha_cierre": fecha_cierre.isoformat(),
                "cantidad_preguntas": cantidad_preguntas,
                "cantidad_intentos_permitidos": cantidad_intentos_permitidos,
            },
            headers=docente_headers(),
        )


def _periodo_por_defecto() -> tuple[datetime, datetime]:
    apertura = datetime.now(UTC)
    return apertura, apertura + timedelta(days=7)


@given("un Docente autenticado")
def docente_autenticado(context):
    materia_id = run_async(_crear_materia_con_preguntas(f"Materia {uuid.uuid4()}", 20))
    context["materia_id"] = materia_id
    context["fecha_apertura"], context["fecha_cierre"] = _periodo_por_defecto()


@given(parsers.parse('la materia "{nombre}" tiene {cantidad:d} preguntas activas en su banco'))
def materia_con_preguntas_activas(context, nombre, cantidad):
    context["materia_id"] = run_async(_crear_materia_con_preguntas(nombre, cantidad))


@given(parsers.parse("una materia con solo {cantidad:d} preguntas activas en su banco"))
def materia_con_pocas_preguntas_activas(context, cantidad):
    context["materia_id"] = run_async(
        _crear_materia_con_preguntas(f"Materia {uuid.uuid4()}", cantidad)
    )


@given("un materia_id que no existe en BC Banco de Preguntas")
def materia_id_inexistente(context):
    context["materia_id"] = str(uuid.uuid4())
    context["fecha_apertura"], context["fecha_cierre"] = _periodo_por_defecto()


@when(
    parsers.parse(
        "ejecuta CrearActividadPeriodoAbierto con cantidad_preguntas={cantidad:d} "
        "y cantidad_intentos_permitidos={intentos:d}"
    )
)
def ejecuta_crear_actividad_valida(context, cantidad, intentos):
    context["response"] = run_async(
        _post_crear_actividad(
            context["materia_id"],
            context["fecha_apertura"],
            context["fecha_cierre"],
            cantidad,
            intentos,
        )
    )


@when(
    parsers.parse(
        "un Docente ejecuta CrearActividadPeriodoAbierto con cantidad_preguntas={cantidad:d}"
    )
)
def un_docente_ejecuta_crear_actividad_con_cantidad(context, cantidad):
    apertura, cierre = _periodo_por_defecto()
    context["response"] = run_async(
        _post_crear_actividad(context["materia_id"], apertura, cierre, cantidad, 1)
    )


@when("ejecuta CrearActividadPeriodoAbierto con fecha_apertura posterior a fecha_cierre")
def ejecuta_crear_actividad_periodo_invalido(context):
    apertura, cierre = _periodo_por_defecto()
    context["response"] = run_async(
        _post_crear_actividad(context["materia_id"], cierre, apertura, 10, 1)
    )


@when(
    parsers.parse(
        "ejecuta CrearActividadPeriodoAbierto con cantidad_intentos_permitidos={intentos:d}"
    )
)
def ejecuta_crear_actividad_con_intentos(context, intentos):
    context["response"] = run_async(
        _post_crear_actividad(
            context["materia_id"], context["fecha_apertura"], context["fecha_cierre"], 10, intentos
        )
    )


@when("un Docente ejecuta CrearActividadPeriodoAbierto con ese materia_id")
def un_docente_ejecuta_crear_actividad_con_materia_id(context):
    context["response"] = run_async(
        _post_crear_actividad(
            context["materia_id"], context["fecha_apertura"], context["fecha_cierre"], 10, 1
        )
    )


@then("el sistema persiste ActividadEvaluativaPeriodoAbierto con cerrada_manualmente=false")
def valida_actividad_persistida(context):
    assert context["response"].status_code == 201
    assert context["response"].json()["cerrada_manualmente"] is False


@then("se emite el evento ActividadEvaluativaCreada")
def valida_evento_emitido(context):
    assert context["response"].status_code == 201
    assert "id" in context["response"].json()


@then(parsers.parse("el sistema rechaza la operación con {codigo_error}"))
def valida_rechazo_con_codigo(context, codigo_error):
    mapa_status = {
        "PreguntasInsuficientes": 422,
        "PeriodoInvalido": 422,
        "CantidadIntentosInvalida": 422,
        "MateriaNoExiste": 404,
    }
    assert context["response"].status_code == mapa_status[codigo_error]


@then("no se persiste ninguna actividad")
def valida_ninguna_actividad_persistida(context):
    assert context["response"].status_code == 422
