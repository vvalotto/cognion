"""Steps BDD de US-4.2.1 (`tests/features/inc4/US-4.2.1-desempeno-estudiante-elegido.feature`)."""

from __future__ import annotations

import asyncio
import uuid
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

scenarios("../../features/inc4/US-4.2.1-desempeno-estudiante-elegido.feature")

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
def limpiar_tablas_analytics():
    run_async(_limpiar_tablas())
    yield
    run_async(_limpiar_tablas())


@pytest.fixture
def context():
    return {"materia_id": uuid4()}


def _headers_docente() -> dict[str, str]:
    jwt_vo = PyJWTIssuer().emitir(uuid4(), TipoPerfil.DOCENTE)
    return {"Authorization": f"Bearer {jwt_vo.token}"}


def _headers_estudiante(estudiante_id) -> dict[str, str]:
    jwt_vo = PyJWTIssuer().emitir(estudiante_id, TipoPerfil.ESTUDIANTE)
    return {"Authorization": f"Bearer {jwt_vo.token}"}


async def _crear_estudiante_real() -> Usuario:
    """Persiste un `Usuario` con rol Estudiante real — lo exige `EstudianteConsultaPort.existe`."""
    async with SessionLocal() as session:
        hasher = BcryptPasswordHasher()
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        comision_repo = SQLAlchemyComisionRepository(session)

        admin = Usuario.crear(
            "Admin",
            f"admin.{uuid.uuid4()}@fiuner.edu.ar",
            hasher.hash("x"),
            TipoPerfil.ADMINISTRADOR,
        )
        await usuario_repo.guardar(admin)
        comision = Comision.crear(uuid.uuid4(), "lu 10-12", admin.id)
        await comision_repo.guardar(comision)

        estudiante = Usuario.crear_estudiante(
            "Estudiante",
            f"estudiante.{uuid.uuid4()}@fiuner.edu.ar",
            hasher.hash("x"),
            comision.id,
        )
        await usuario_repo.guardar(estudiante)
        return estudiante


async def _crear_actividad(store: SQLAlchemyEventStore, actividad_id, materia_id) -> None:
    await store.append(
        AGGREGATE_TYPE_ACTIVIDAD,
        actividad_id,
        0,
        [
            EventoParaAlmacenar(
                "ActividadEvaluativaCreada",
                {"actividad_id": str(actividad_id), "materia_id": str(materia_id)},
            )
        ],
    )


async def _iniciar_evaluacion(
    store: SQLAlchemyEventStore, evaluacion_id, actividad_id, estudiante_id
) -> int:
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
                },
            )
        ],
    )
    return 1


async def _registrar_respuesta(
    store: SQLAlchemyEventStore, evaluacion_id, seq: int, es_correcta: bool
) -> int:
    await store.append(
        AGGREGATE_TYPE_EVALUACION,
        evaluacion_id,
        seq,
        [
            EventoParaAlmacenar(
                "RespuestaRegistrada",
                {
                    "respuesta_id": str(uuid4()),
                    "evaluacion_id": str(evaluacion_id),
                    "pregunta_id": str(uuid4()),
                    "numero_intento": 1,
                    "contenido": {},
                    "es_correcta": es_correcta,
                },
            )
        ],
    )
    return seq + 1


async def _finalizar_evaluacion(store: SQLAlchemyEventStore, evaluacion_id, seq: int) -> int:
    await store.append(
        AGGREGATE_TYPE_EVALUACION,
        evaluacion_id,
        seq,
        [
            EventoParaAlmacenar(
                "EvaluacionFinalizada", {"evaluacion_id": str(evaluacion_id), "actor": "estudiante"}
            )
        ],
    )
    return seq + 1


async def _crear_evaluacion_finalizada(
    store: SQLAlchemyEventStore, actividad_id, estudiante_id, correctas: int, incorrectas: int
) -> None:
    evaluacion_id = uuid4()
    seq = await _iniciar_evaluacion(store, evaluacion_id, actividad_id, estudiante_id)
    for _ in range(correctas):
        seq = await _registrar_respuesta(store, evaluacion_id, seq, True)
    for _ in range(incorrectas):
        seq = await _registrar_respuesta(store, evaluacion_id, seq, False)
    await _finalizar_evaluacion(store, evaluacion_id, seq)


@given("un Docente autenticado y un Estudiante con 2 Evaluacion finalizadas en la materia X")
def docente_y_estudiante_con_dos_evaluaciones(context):
    async def _setup():
        estudiante = await _crear_estudiante_real()
        async with SessionLocal() as session:
            store = SQLAlchemyEventStore(session)
            actividad_id = uuid4()
            await _crear_actividad(store, actividad_id, context["materia_id"])
            await _crear_evaluacion_finalizada(store, actividad_id, estudiante.id, 8, 2)
            await _crear_evaluacion_finalizada(store, actividad_id, estudiante.id, 5, 3)
        return estudiante

    context["estudiante"] = run_async(_setup())
    context["headers"] = _headers_docente()


@given("un Docente autenticado y un Estudiante sin ninguna Evaluacion finalizada en la materia Y")
def docente_y_estudiante_sin_evaluaciones(context):
    context["estudiante"] = run_async(_crear_estudiante_real())
    context["headers"] = _headers_docente()


@given("un Docente autenticado")
def docente_autenticado(context):
    context["headers"] = _headers_docente()
    context["estudiante_id_inexistente"] = uuid4()


@given("una request sin JWT válido")
def request_sin_jwt(context):
    context["headers"] = None
    context["estudiante_id_inexistente"] = uuid4()


@given("un Estudiante autenticado")
def estudiante_autenticado(context):
    context["headers"] = _headers_estudiante(uuid4())
    context["otro_estudiante_id"] = uuid4()


def _get(context, materia_id, estudiante_id, headers) -> None:
    async def _call():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(
                f"/analytics/materias/{materia_id}/estudiantes/{estudiante_id}/desempeno",
                headers=headers,
            )

    context["response"] = run_async(_call())


@when("el Docente hace GET /analytics/materias/X/estudiantes/{estudiante_id}/desempeno")
def docente_hace_get_materia_x(context):
    _get(context, context["materia_id"], context["estudiante"].id, context["headers"])


@when("el Docente hace GET /analytics/materias/Y/estudiantes/{estudiante_id}/desempeno")
def docente_hace_get_materia_y(context):
    _get(context, context["materia_id"], context["estudiante"].id, context["headers"])


@when("hace GET /analytics/materias/X/estudiantes/{id-inexistente}/desempeno")
def hace_get_estudiante_inexistente(context):
    _get(context, context["materia_id"], context["estudiante_id_inexistente"], context["headers"])


@when("hace GET /analytics/materias/X/estudiantes/{estudiante_id}/desempeno")
def hace_get_sin_jwt(context):
    _get(context, context["materia_id"], context["estudiante_id_inexistente"], context["headers"])


@when("hace GET /analytics/materias/X/estudiantes/{otro_estudiante_id}/desempeno")
def hace_get_otro_estudiante(context):
    _get(context, context["materia_id"], context["otro_estudiante_id"], context["headers"])


@then('recibe 200 con 2 filas en "evaluaciones" y el "resumen" acumulado correcto')
def valida_200_con_dos_filas_y_resumen(context):
    response = context["response"]
    assert response.status_code == 200
    data = response.json()
    assert len(data["evaluaciones"]) == 2
    assert data["resumen"] == {
        "total_correctas": 13,
        "total_incorrectas": 5,
        "porcentaje_acierto": 72,
        "cantidad_evaluaciones": 2,
    }


@then(
    'recibe 200 con "evaluaciones": [] y "resumen" en cero, sin dividir por cero en '
    "porcentaje_acierto"
)
def valida_200_vacio_y_resumen_en_cero(context):
    response = context["response"]
    assert response.status_code == 200
    data = response.json()
    assert data["evaluaciones"] == []
    assert data["resumen"] == {
        "total_correctas": 0,
        "total_incorrectas": 0,
        "porcentaje_acierto": 0,
        "cantidad_evaluaciones": 0,
    }


@then("recibe 404")
def valida_404(context):
    assert context["response"].status_code == 404


@then("recibe 401")
def valida_401(context):
    assert context["response"].status_code == 401


@then("recibe 403")
def valida_403(context):
    assert context["response"].status_code == 403
