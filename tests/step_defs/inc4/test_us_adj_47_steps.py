"""Steps BDD de US-ADJ-47
(`tests/features/inc5-adj/US-ADJ-47-completitud-por-actividad.feature`)."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, scenarios, then, when
from sqlalchemy import text

from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.frameworks.event_store.sqlalchemy_event_store import (
    SQLAlchemyEventStore,
)
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

scenarios("../../features/inc5-adj/US-ADJ-47-completitud-por-actividad.feature")

AGGREGATE_TYPE_EVALUACION = "Evaluacion"
AGGREGATE_TYPE_ACTIVIDAD = "ActividadEvaluativaPeriodoAbierto"


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM events"))
        await session.execute(text("DELETE FROM estudiante"))
        await session.execute(text("DELETE FROM comision"))
        await session.execute(text("DELETE FROM docente"))
        await session.execute(text("DELETE FROM administrador"))
        await session.execute(text("DELETE FROM usuario"))
        await session.commit()


@pytest.fixture(autouse=True)
def limpiar_tablas_us_adj_47():
    run_async(_limpiar_tablas())
    yield
    run_async(_limpiar_tablas())


@pytest.fixture
def context():
    return {}


def _headers_docente() -> dict[str, str]:
    jwt_vo = PyJWTIssuer().emitir(uuid4(), TipoPerfil.DOCENTE)
    return {"Authorization": f"Bearer {jwt_vo.token}"}


def _headers_estudiante() -> dict[str, str]:
    jwt_vo = PyJWTIssuer().emitir(uuid4(), TipoPerfil.ESTUDIANTE)
    return {"Authorization": f"Bearer {jwt_vo.token}"}


async def _comision_con_estudiantes(session, materia_id, cantidad: int):
    hasher = BcryptPasswordHasher()
    usuario_repo = SQLAlchemyUsuarioRepository(session)
    comision_repo = SQLAlchemyComisionRepository(session)

    admin = Usuario.crear(
        "Admin", f"admin.{uuid.uuid4()}@fiuner.edu.ar", hasher.hash("x"), TipoPerfil.ADMINISTRADOR
    )
    await usuario_repo.guardar(admin)
    comision = Comision.crear(materia_id, "lu 10-12", admin.id)
    await comision_repo.guardar(comision)

    estudiantes = []
    for _ in range(cantidad):
        estudiante = Usuario.crear_estudiante(
            "Estudiante", f"estudiante.{uuid.uuid4()}@fiuner.edu.ar", hasher.hash("x"), comision.id
        )
        await usuario_repo.guardar(estudiante)
        estudiantes.append(estudiante)
    return comision, estudiantes


async def _iniciar_evaluacion(
    store: SQLAlchemyEventStore, actividad_id, estudiante_id
) -> uuid.UUID:
    """Payload completo de `EvaluacionIniciada` — `listar_estados_de_actividad` (`US-ADJ-47`)
    reconstruye la entidad completa con `Evaluacion.reconstruir()`.
    """
    evaluacion_id = uuid4()
    await store.append(
        AGGREGATE_TYPE_EVALUACION,
        evaluacion_id,
        0,
        [
            EventoParaAlmacenar(
                "EvaluacionIniciada",
                {
                    "evaluacion_id": str(evaluacion_id),
                    "actividad_id": str(actividad_id),
                    "estudiante_id": str(estudiante_id),
                    "ocurrido_en": datetime.now(UTC).isoformat(),
                    "preguntas_asignadas": [],
                },
            )
        ],
    )
    return evaluacion_id


async def _suspender(store: SQLAlchemyEventStore, evaluacion_id) -> None:
    await store.append(
        AGGREGATE_TYPE_EVALUACION,
        evaluacion_id,
        1,
        [EventoParaAlmacenar("EvaluacionSuspendida", {"actor": "estudiante"})],
    )


async def _finalizar(store: SQLAlchemyEventStore, evaluacion_id) -> None:
    await store.append(
        AGGREGATE_TYPE_EVALUACION,
        evaluacion_id,
        1,
        [EventoParaAlmacenar("EvaluacionFinalizada", {"actor": "estudiante"})],
    )


async def _actividad_creada(
    store: SQLAlchemyEventStore, actividad_id, materia_id, comisiones_ids: frozenset | None = None
) -> None:
    """Payload completo — `obtener_actividad_resumen` (`US-ADJ-47`) reconstruye la entidad
    completa con `ActividadEvaluativaPeriodoAbierto.reconstruir()`.
    """
    ahora = datetime.now(UTC)
    await store.append(
        AGGREGATE_TYPE_ACTIVIDAD,
        actividad_id,
        0,
        [
            EventoParaAlmacenar(
                "ActividadEvaluativaCreada",
                {
                    "actividad_id": str(actividad_id),
                    "materia_id": str(materia_id),
                    "fecha_apertura": ahora.isoformat(),
                    "fecha_cierre": ahora.isoformat(),
                    "cantidad_preguntas": 5,
                    "cantidad_intentos_permitidos": 1,
                    "titulo": "Actividad de prueba",
                    "comisiones_ids": [str(c) for c in (comisiones_ids or frozenset())],
                    "unidad_tematica": None,
                    "tema": None,
                    "ocurrido_en": ahora.isoformat(),
                },
            )
        ],
    )


@given("una actividad restringida a la comisión C1 con 4 estudiantes")
def actividad_restringida_con_cuatro_estudiantes(context):
    async def _setup():
        async with SessionLocal() as session:
            materia_id = uuid4()
            comision, estudiantes = await _comision_con_estudiantes(session, materia_id, 4)
            store = SQLAlchemyEventStore(session)
            actividad_id = uuid4()
            await _actividad_creada(store, actividad_id, materia_id, frozenset({comision.id}))
            return actividad_id, estudiantes

    context["actividad_id"], context["estudiantes"] = run_async(_setup())
    context["headers"] = _headers_docente()


@given("1 finalizó, 1 está en curso, 1 suspendió y 1 nunca inició")
def estados_mixtos(context):
    finalizo, en_curso, suspendio, _nunca_inicio = context["estudiantes"]

    async def _setup():
        async with SessionLocal() as session:
            store = SQLAlchemyEventStore(session)
            evaluacion_finalizo = await _iniciar_evaluacion(
                store, context["actividad_id"], finalizo.id
            )
            await _finalizar(store, evaluacion_finalizo)
            await _iniciar_evaluacion(store, context["actividad_id"], en_curso.id)
            evaluacion_suspendio = await _iniciar_evaluacion(
                store, context["actividad_id"], suspendio.id
            )
            await _suspender(store, evaluacion_suspendio)

    run_async(_setup())


@given("una actividad sin comisiones_ids visible a toda la materia con 2 comisiones")
def actividad_sin_restriccion_dos_comisiones(context):
    async def _setup():
        async with SessionLocal() as session:
            materia_id = uuid4()
            _comision_1, estudiantes_1 = await _comision_con_estudiantes(session, materia_id, 1)
            _comision_2, estudiantes_2 = await _comision_con_estudiantes(session, materia_id, 1)
            store = SQLAlchemyEventStore(session)
            actividad_id = uuid4()
            await _actividad_creada(store, actividad_id, materia_id)
            return actividad_id, estudiantes_1 + estudiantes_2

    context["actividad_id"], context["estudiantes"] = run_async(_setup())
    context["headers"] = _headers_docente()


@given("un actividad_id que no corresponde a ninguna actividad")
def actividad_inexistente(context):
    context["actividad_id"] = uuid4()
    context["headers"] = _headers_docente()


@given("un Estudiante autenticado")
def estudiante_autenticado(context):
    context["actividad_id"] = uuid4()
    context["headers"] = _headers_estudiante()


def _get(context) -> None:
    async def _call():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(
                f"/analytics/actividades/{context['actividad_id']}/completitud",
                headers=context["headers"],
            )

    context["response"] = run_async(_call())


@when("un Docente hace GET /analytics/actividades/X/completitud")
def docente_hace_get(context):
    _get(context)


@when("un Docente consulta su completitud")
def docente_consulta_completitud(context):
    _get(context)


@when("hace GET /analytics/actividades/X/completitud")
def hace_get(context):
    _get(context)


@then("recibe 200 con resumen finalizadas 1, en_curso 1, suspendidas 1, sin_iniciar 1")
def valida_200_resumen_mixto(context):
    response = context["response"]
    assert response.status_code == 200
    data = response.json()
    assert data["resumen"] == {
        "finalizadas": 1,
        "en_curso": 1,
        "suspendidas": 1,
        "sin_iniciar": 1,
    }


@then("el detalle lista los 4 estudiantes con su estado exacto")
def valida_detalle_cuatro_estudiantes(context):
    data = context["response"].json()
    finalizo, en_curso, suspendio, nunca_inicio = context["estudiantes"]
    estados_por_id = {fila["estudiante_id"]: fila["estado"] for fila in data["detalle"]}
    assert len(data["detalle"]) == 4
    assert estados_por_id[str(finalizo.id)] == "finalizada"
    assert estados_por_id[str(en_curso.id)] == "en_curso"
    assert estados_por_id[str(suspendio.id)] == "suspendida"
    assert estados_por_id[str(nunca_inicio.id)] == "sin_iniciar"


@then("el roster del detalle incluye los estudiantes de ambas comisiones")
def valida_roster_ambas_comisiones(context):
    data = context["response"].json()
    esperados = {str(estudiante.id) for estudiante in context["estudiantes"]}
    assert {fila["estudiante_id"] for fila in data["detalle"]} == esperados


@then("recibe 404")
def valida_404(context):
    assert context["response"].status_code == 404


@then("recibe 403")
def valida_403(context):
    assert context["response"].status_code == 403
