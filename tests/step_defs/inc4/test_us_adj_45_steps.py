"""Steps BDD de US-ADJ-45 (`tests/features/inc5-adj/US-ADJ-45-evolucion-temporal.feature`)."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta
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

scenarios("../../features/inc5-adj/US-ADJ-45-evolucion-temporal.feature")

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
def limpiar_tablas_us_adj_45():
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


async def _comision_con_estudiante(session, materia_id):
    hasher = BcryptPasswordHasher()
    usuario_repo = SQLAlchemyUsuarioRepository(session)
    comision_repo = SQLAlchemyComisionRepository(session)

    admin = Usuario.crear(
        "Admin", f"admin.{uuid.uuid4()}@fiuner.edu.ar", hasher.hash("x"), TipoPerfil.ADMINISTRADOR
    )
    await usuario_repo.guardar(admin)
    comision = Comision.crear(materia_id, "lu 10-12", admin.id)
    await comision_repo.guardar(comision)

    estudiante = Usuario.crear_estudiante(
        "Estudiante", f"estudiante.{uuid.uuid4()}@fiuner.edu.ar", hasher.hash("x"), comision.id
    )
    await usuario_repo.guardar(estudiante)
    return comision, estudiante


async def _actividad_creada(
    store: SQLAlchemyEventStore, actividad_id, materia_id, titulo: str = ""
) -> None:
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
                    "fecha_apertura": (ahora - timedelta(days=10)).isoformat(),
                    "fecha_cierre": (ahora + timedelta(days=10)).isoformat(),
                    "cantidad_preguntas": 1,
                    "cantidad_intentos_permitidos": 1,
                    "titulo": titulo,
                    "comisiones_ids": [],
                    "unidad_tematica": None,
                    "tema": None,
                    "ocurrido_en": (ahora - timedelta(days=10)).isoformat(),
                },
            )
        ],
    )


async def _evaluacion_finalizada(
    store: SQLAlchemyEventStore,
    actividad_id,
    estudiante_id,
    finalizada_en: datetime,
    es_correcta: bool = True,
) -> None:
    evaluacion_id, pregunta_id = uuid4(), uuid4()
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
                    "preguntas_asignadas": [{"pregunta_id": str(pregunta_id), "orden": 0}],
                    "ocurrido_en": (finalizada_en - timedelta(minutes=10)).isoformat(),
                },
            )
        ],
    )
    await store.append(
        AGGREGATE_TYPE_EVALUACION,
        evaluacion_id,
        1,
        [
            EventoParaAlmacenar(
                "RespuestaRegistrada",
                {
                    "respuesta_id": str(uuid4()),
                    "evaluacion_id": str(evaluacion_id),
                    "pregunta_id": str(pregunta_id),
                    "numero_intento": 1,
                    "contenido": {},
                    "es_correcta": es_correcta,
                    "ocurrido_en": (finalizada_en - timedelta(minutes=5)).isoformat(),
                },
            )
        ],
    )
    await store.append(
        AGGREGATE_TYPE_EVALUACION,
        evaluacion_id,
        2,
        [
            EventoParaAlmacenar(
                "EvaluacionFinalizada",
                {
                    "evaluacion_id": str(evaluacion_id),
                    "actor": "estudiante",
                    "ocurrido_en": finalizada_en.isoformat(),
                },
            )
        ],
    )


@given("un estudiante con 3 Evaluacion finalizadas en distintas fechas y % de acierto")
def estudiante_con_tres_evaluaciones(context):
    async def _setup():
        async with SessionLocal() as session:
            materia_id = uuid4()
            _comision, estudiante = await _comision_con_estudiante(session, materia_id)
            store = SQLAlchemyEventStore(session)
            base = datetime.now(UTC) - timedelta(days=30)
            actividades = []
            for i, es_correcta in enumerate([True, False, True]):
                actividad_id = uuid4()
                await _actividad_creada(store, actividad_id, materia_id, titulo=f"Parcial {i + 1}")
                await _evaluacion_finalizada(
                    store,
                    actividad_id,
                    estudiante.id,
                    base + timedelta(days=i * 10),
                    es_correcta=es_correcta,
                )
                actividades.append(actividad_id)
            return materia_id, estudiante.id, actividades

    context["materia_id"], context["estudiante_id"], context["actividades"] = run_async(_setup())
    context["headers"] = _headers_docente()


@given("una comisión de 3 estudiantes donde solo 2 finalizaron la actividad A")
def comision_con_participacion_parcial(context):
    async def _setup():
        async with SessionLocal() as session:
            materia_id = uuid4()
            comision, estudiante_1 = await _comision_con_estudiante(session, materia_id)
            usuario_repo = SQLAlchemyUsuarioRepository(session)
            hasher = BcryptPasswordHasher()
            estudiante_2 = Usuario.crear_estudiante(
                "E2", f"e2.{uuid.uuid4()}@fiuner.edu.ar", hasher.hash("x"), comision.id
            )
            await usuario_repo.guardar(estudiante_2)
            estudiante_3 = Usuario.crear_estudiante(
                "E3", f"e3.{uuid.uuid4()}@fiuner.edu.ar", hasher.hash("x"), comision.id
            )
            await usuario_repo.guardar(estudiante_3)

            store = SQLAlchemyEventStore(session)
            actividad_a = uuid4()
            await _actividad_creada(store, actividad_a, materia_id, titulo="Actividad A")
            ahora = datetime.now(UTC) - timedelta(days=1)
            await _evaluacion_finalizada(store, actividad_a, estudiante_1.id, ahora, True)
            await _evaluacion_finalizada(store, actividad_a, estudiante_2.id, ahora, False)
            return materia_id, comision.id

    context["materia_id"], context["comision_id"] = run_async(_setup())
    context["headers"] = _headers_docente()


@given("un estudiante sin ninguna Evaluacion finalizada en la materia")
def estudiante_sin_evaluaciones(context):
    async def _setup():
        async with SessionLocal() as session:
            materia_id = uuid4()
            _comision, estudiante = await _comision_con_estudiante(session, materia_id)
            return materia_id, estudiante.id

    context["materia_id"], context["estudiante_id"] = run_async(_setup())
    context["headers"] = _headers_docente()


@given("una comisión de otra materia")
def comision_de_otra_materia(context):
    async def _setup():
        async with SessionLocal() as session:
            materia_id = uuid4()
            otra_materia_id = uuid4()
            comision, _estudiante = await _comision_con_estudiante(session, otra_materia_id)
            return materia_id, comision.id

    context["materia_id"], context["comision_id"] = run_async(_setup())
    context["headers"] = _headers_docente()


@given("una request sin JWT válido")
def request_sin_jwt(context):
    context["materia_id"], context["estudiante_id"], context["comision_id"] = (
        uuid4(),
        uuid4(),
        uuid4(),
    )
    context["headers"] = None


@given("un Estudiante autenticado")
def estudiante_autenticado(context):
    context["materia_id"], context["estudiante_id"], context["comision_id"] = (
        uuid4(),
        uuid4(),
        uuid4(),
    )
    context["headers"] = _headers_estudiante()


@when("un Docente hace GET .../estudiantes/{id}/evolucion-temporal")
def docente_hace_get_evolucion_estudiante(context):
    async def _call():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(
                f"/analytics/materias/{context['materia_id']}/estudiantes/{context['estudiante_id']}/evolucion-temporal",
                headers=context["headers"],
            )

    context["response"] = run_async(_call())


@when("un Docente hace GET .../comisiones/{id}/evolucion-temporal")
def docente_hace_get_evolucion_comision(context):
    async def _call():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(
                f"/analytics/materias/{context['materia_id']}/comisiones/{context['comision_id']}/evolucion-temporal",
                headers=context["headers"],
            )

    context["response"] = run_async(_call())


@when("un Docente consulta su evolución")
def docente_consulta_evolucion(context):
    docente_hace_get_evolucion_estudiante(context)


@when("un Docente hace GET /analytics/materias/X/comisiones/{esa comisión}/evolucion-temporal")
def docente_hace_get_comision_de_otra_materia(context):
    docente_hace_get_evolucion_comision(context)


@when("hace GET .../evolucion-temporal")
def hace_get_evolucion_temporal(context):
    """Ambos endpoints comparten el mismo guard de rol (`require_docente`) — el resultado de
    401/403 es idéntico sin importar cuál se elija, se usa el individual por simplicidad."""
    docente_hace_get_evolucion_estudiante(context)


@then("recibe 200 con 3 puntos ordenados cronológicamente, cada uno con el título de su actividad")
def valida_200_tres_puntos_ordenados(context):
    response = context["response"]
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert [punto["actividad_id"] for punto in data] == [
        str(actividad_id) for actividad_id in context["actividades"]
    ]
    assert all(punto["titulo_actividad"] for punto in data)


@then("el punto de la actividad A promedia solo esos 2 estudiantes, no los 3")
def valida_promedio_solo_2_estudiantes(context):
    response = context["response"]
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["porcentaje_aciertos_promedio"] == 50.0


@then("recibe 200 con lista vacía")
def valida_200_lista_vacia(context):
    response = context["response"]
    assert response.status_code == 200
    assert response.json() == []


@then("recibe 422")
def valida_422(context):
    assert context["response"].status_code == 422


@then("recibe 401")
def valida_401(context):
    assert context["response"].status_code == 401


@then("recibe 403")
def valida_403(context):
    assert context["response"].status_code == 403
