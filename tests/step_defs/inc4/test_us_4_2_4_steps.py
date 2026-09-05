"""Steps BDD de US-4.2.4 (`tests/features/inc4/US-4.2.4-tasa-error-por-tema.feature`)."""

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
from src.banco_preguntas.entities.banco import Banco
from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.importancia import Importancia
from src.banco_preguntas.entities.materia import Materia
from src.banco_preguntas.entities.metadatos_pregunta import MetadatosPregunta
from src.banco_preguntas.entities.opcion import Opcion
from src.banco_preguntas.entities.pregunta_plantilla import PreguntaPlantillaOpcionMultiple
from src.banco_preguntas.interface_adapters.gateways.banco_repository import (
    SQLAlchemyBancoRepository,
)
from src.banco_preguntas.interface_adapters.gateways.materia_repository import (
    SQLAlchemyMateriaRepository,
)
from src.banco_preguntas.interface_adapters.gateways.pregunta_repository import (
    SQLAlchemyPreguntaRepository,
)
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

scenarios("../../features/inc4/US-4.2.4-tasa-error-por-tema.feature")

AGGREGATE_TYPE_EVALUACION = "Evaluacion"
AGGREGATE_TYPE_ACTIVIDAD = "ActividadEvaluativaPeriodoAbierto"


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM events"))
        await session.execute(text("DELETE FROM pregunta_plantilla"))
        await session.execute(text("DELETE FROM banco"))
        await session.execute(text("DELETE FROM materia"))
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
    return {}


def _headers_docente() -> dict[str, str]:
    jwt_vo = PyJWTIssuer().emitir(uuid4(), TipoPerfil.DOCENTE)
    return {"Authorization": f"Bearer {jwt_vo.token}"}


def _headers_estudiante() -> dict[str, str]:
    jwt_vo = PyJWTIssuer().emitir(uuid4(), TipoPerfil.ESTUDIANTE)
    return {"Authorization": f"Bearer {jwt_vo.token}"}


async def _materia_con_banco_y_pregunta(session, unidad_tematica: str, tema: str):
    materia_repo = SQLAlchemyMateriaRepository(session)
    banco_repo = SQLAlchemyBancoRepository(session)
    pregunta_repo = SQLAlchemyPreguntaRepository(session)
    materia = Materia.crear(f"Ingeniería de Software {uuid.uuid4()}")
    await materia_repo.guardar(materia)
    banco = Banco.crear(materia.id)
    await banco_repo.guardar(banco)
    pregunta = PreguntaPlantillaOpcionMultiple.crear(
        banco_id=banco.id,
        metadatos=MetadatosPregunta(
            texto=f"Pregunta {uuid.uuid4()}",
            unidad_tematica=unidad_tematica,
            tema=tema,
            dificultad=Dificultad.MEDIO,
            importancia=Importancia.ALTO,
        ),
        opciones=[Opcion(texto="A", es_correcta=True), Opcion(texto="B", es_correcta=False)],
    )
    await pregunta_repo.guardar(pregunta)
    return materia, pregunta.id


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


async def _actividad_creada(store: SQLAlchemyEventStore, actividad_id, materia_id) -> None:
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


async def _evaluacion_finalizada_con_respuesta(
    store: SQLAlchemyEventStore, actividad_id, estudiante_id, pregunta_id, es_correcta: bool
) -> None:
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
                "EvaluacionFinalizada", {"evaluacion_id": str(evaluacion_id), "actor": "estudiante"}
            )
        ],
    )


@given("una materia con Evaluacion finalizadas de 2 comisiones distintas")
def materia_con_evaluaciones_de_dos_comisiones(context):
    async def _setup():
        async with SessionLocal() as session:
            materia, pregunta_id = await _materia_con_banco_y_pregunta(
                session, "Unidad 1", "Herencia"
            )
            comision_1, estudiante_1 = await _comision_con_estudiante(session, materia.id)
            _, estudiante_2 = await _comision_con_estudiante(session, materia.id)

            store = SQLAlchemyEventStore(session)
            actividad_id = uuid4()
            await _actividad_creada(store, actividad_id, materia.id)
            await _evaluacion_finalizada_con_respuesta(
                store, actividad_id, estudiante_1.id, pregunta_id, False
            )
            await _evaluacion_finalizada_con_respuesta(
                store, actividad_id, estudiante_2.id, pregunta_id, True
            )
            return materia.id, comision_1.id

    context["materia_id"], context["comision_id"] = run_async(_setup())
    context["headers"] = _headers_docente()


@given("la misma materia de arriba")
def la_misma_materia_de_arriba(context):
    """Escenarios BDD son independientes entre sí — reconstruye el mismo setup del escenario
    anterior en vez de asumir continuidad de contexto."""
    materia_con_evaluaciones_de_dos_comisiones(context)


@given("una materia sin ninguna Evaluacion finalizada")
def materia_sin_evaluaciones(context):
    context["materia_id"] = uuid4()
    context["headers"] = _headers_docente()


@given("una comisión de otra materia")
def comision_de_otra_materia(context):
    async def _setup():
        async with SessionLocal() as session:
            materia, _ = await _materia_con_banco_y_pregunta(session, "Unidad 1", "Herencia")
            otra_materia_id = uuid4()
            comision, _ = await _comision_con_estudiante(session, otra_materia_id)
            return materia.id, comision.id

    context["materia_id"], context["comision_id"] = run_async(_setup())
    context["headers"] = _headers_docente()


@given("una request sin JWT válido")
def request_sin_jwt(context):
    context["materia_id"] = uuid4()
    context["headers"] = None


@given("un Estudiante autenticado")
def estudiante_autenticado(context):
    context["materia_id"] = uuid4()
    context["headers"] = _headers_estudiante()


def _get(context, comision_id=None) -> None:
    async def _call():
        params = {"comision_id": str(comision_id)} if comision_id is not None else None
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(
                f"/analytics/materias/{context['materia_id']}/tasa-error-por-tema",
                params=params,
                headers=context["headers"],
            )

    context["response"] = run_async(_call())


@when("un Docente hace GET /analytics/materias/X/tasa-error-por-tema")
def docente_hace_get_sin_comision(context):
    _get(context)


@when("un Docente hace GET /analytics/materias/X/tasa-error-por-tema?comision_id=C1")
def docente_hace_get_con_comision(context):
    _get(context, comision_id=context["comision_id"])


@when("un Docente hace GET /analytics/materias/Y/tasa-error-por-tema")
def hace_get_materia_y(context):
    _get(context)


@when("un Docente hace GET /analytics/materias/X/tasa-error-por-tema?comision_id={esa comisión}")
def hace_get_con_comision_de_otra_materia(context):
    _get(context, comision_id=context["comision_id"])


@when("hace GET /analytics/materias/X/tasa-error-por-tema")
def hace_get_sin_comision(context):
    _get(context)


@then("recibe 200 con la tasa de error agregada de ambas comisiones, ordenada descendente")
def valida_200_agregado_ambas_comisiones(context):
    response = context["response"]
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["cantidad_respuestas"] == 2
    assert data[0]["cantidad_incorrectas"] == 1
    assert data[0]["tasa_error"] == 0.5


@then("recibe 200 con la tasa de error calculada solo sobre los estudiantes de C1")
def valida_200_acotado_a_c1(context):
    response = context["response"]
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["cantidad_respuestas"] == 1
    assert data[0]["cantidad_incorrectas"] == 1
    assert data[0]["tasa_error"] == 1.0


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
