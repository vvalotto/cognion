"""Steps BDD de US-ADJ-44
(`tests/features/inc5-adj/US-ADJ-44-desempeno-por-comision.feature`)."""

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
from src.banco_preguntas.entities.banco import Banco
from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.importancia import Importancia
from src.banco_preguntas.entities.materia import Materia
from src.banco_preguntas.entities.metadatos_pregunta import MetadatosPregunta
from src.banco_preguntas.entities.pregunta_plantilla import PreguntaPlantillaVerdaderoFalso
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

scenarios("../../features/inc5-adj/US-ADJ-44-desempeno-por-comision.feature")

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
def limpiar_tablas_us_adj_44():
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


def _headers_administrador() -> dict[str, str]:
    jwt_vo = PyJWTIssuer().emitir(uuid4(), TipoPerfil.ADMINISTRADOR)
    return {"Authorization": f"Bearer {jwt_vo.token}"}


async def _comision_con_dos_estudiantes(session, materia_id):
    hasher = BcryptPasswordHasher()
    usuario_repo = SQLAlchemyUsuarioRepository(session)
    comision_repo = SQLAlchemyComisionRepository(session)

    admin = Usuario.crear(
        "Admin", f"admin.{uuid.uuid4()}@fiuner.edu.ar", hasher.hash("x"), TipoPerfil.ADMINISTRADOR
    )
    await usuario_repo.guardar(admin)
    comision = Comision.crear(materia_id, "lu 10-12", admin.id)
    await comision_repo.guardar(comision)

    estudiante_1 = Usuario.crear_estudiante(
        "Estudiante Uno", f"e1.{uuid.uuid4()}@fiuner.edu.ar", hasher.hash("x"), comision.id
    )
    await usuario_repo.guardar(estudiante_1)
    estudiante_2 = Usuario.crear_estudiante(
        "Estudiante Dos", f"e2.{uuid.uuid4()}@fiuner.edu.ar", hasher.hash("x"), comision.id
    )
    await usuario_repo.guardar(estudiante_2)
    return comision, estudiante_1, estudiante_2


async def _comision_con_un_estudiante(session, materia_id):
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


async def _actividad_cerrada_creada(store: SQLAlchemyEventStore, actividad_id, materia_id) -> None:
    """Actividad ya vencida — sirve de origen de una `Evaluacion` finalizada, sin contar como
    pendiente en `listar_actividades_abiertas` (`US-ADJ-44`)."""
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
                    "fecha_cierre": (ahora - timedelta(days=1)).isoformat(),
                    "cantidad_preguntas": 1,
                    "cantidad_intentos_permitidos": 1,
                    "titulo": "",
                    "comisiones_ids": [],
                    "unidad_tematica": None,
                    "tema": None,
                    "ocurrido_en": (ahora - timedelta(days=10)).isoformat(),
                },
            )
        ],
    )


async def _actividad_abierta_creada(
    store: SQLAlchemyEventStore, actividad_id, materia_id, comisiones_ids
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
                    "fecha_apertura": (ahora - timedelta(days=1)).isoformat(),
                    "fecha_cierre": (ahora + timedelta(days=7)).isoformat(),
                    "cantidad_preguntas": 1,
                    "cantidad_intentos_permitidos": 1,
                    "titulo": "",
                    "comisiones_ids": [str(c) for c in comisiones_ids],
                    "unidad_tematica": None,
                    "tema": None,
                    "ocurrido_en": (ahora - timedelta(days=1)).isoformat(),
                },
            )
        ],
    )


async def _pregunta_persistida(session, banco_id) -> uuid.UUID:
    """Pregunta real en Banco de Preguntas — necesaria para `GET /evaluaciones/{id}/revision`,
    que resuelve `obtener_detalle_correccion` contra la tabla real (`US-3.2.3`)."""
    pregunta_repo = SQLAlchemyPreguntaRepository(session)
    pregunta = PreguntaPlantillaVerdaderoFalso.crear(
        banco_id=banco_id,
        metadatos=MetadatosPregunta(
            texto=f"Pregunta {uuid.uuid4()}",
            unidad_tematica="Unidad 1",
            tema="Tema",
            dificultad=Dificultad.MEDIO,
            importancia=Importancia.ALTO,
        ),
        respuesta_correcta=True,
    )
    await pregunta_repo.guardar(pregunta)
    return pregunta.id


async def _evaluacion_finalizada(
    store: SQLAlchemyEventStore,
    actividad_id,
    estudiante_id,
    es_correcta: bool = True,
    pregunta_id: uuid.UUID | None = None,
) -> uuid.UUID:
    """Arma una `Evaluacion` `Finalizada` con una única pregunta asignada y respondida.

    `preguntas_asignadas` es obligatorio en el payload real de `EvaluacionIniciada`
    (`Evaluacion.reconstruir()`, a diferencia de la lectura cruda del adapter de Analytics, que
    no lo necesita) — insumo del escenario de drill-down a `GET /evaluaciones/{id}/revision`.
    `pregunta_id` real (persistida) solo hace falta para ese escenario; el resto usa un id
    cualquiera, ya que Analytics no resuelve el detalle de la pregunta.
    """
    evaluacion_id = uuid4()
    pregunta_id = pregunta_id or uuid4()
    ahora = datetime.now(UTC)
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
                    "ocurrido_en": ahora.isoformat(),
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
                    "ocurrido_en": (ahora + timedelta(minutes=1)).isoformat(),
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
                    "ocurrido_en": (ahora + timedelta(minutes=2)).isoformat(),
                },
            )
        ],
    )
    return evaluacion_id


@given("una comisión con un estudiante con 2 Evaluacion finalizadas y otro sin ninguna")
def comision_con_estudiantes_en_distinto_estado(context):
    """Estudiante 1 arranca con 1 Evaluacion finalizada (de una actividad ya cerrada) — la
    2° llega en el step siguiente, sobre la actividad abierta ahora (mismo criterio que
    "el segundo estudiante no rindió" implica que el primero sí la rindió)."""

    async def _setup():
        async with SessionLocal() as session:
            materia_id = uuid4()
            comision, estudiante_1, estudiante_2 = await _comision_con_dos_estudiantes(
                session, materia_id
            )
            store = SQLAlchemyEventStore(session)
            actividad_cerrada = uuid4()
            await _actividad_cerrada_creada(store, actividad_cerrada, materia_id)
            await _evaluacion_finalizada(store, actividad_cerrada, estudiante_1.id, True)
            return materia_id, comision.id, estudiante_1.id, estudiante_2.id

    (
        context["materia_id"],
        context["comision_id"],
        context["estudiante_1_id"],
        context["estudiante_2_id"],
    ) = run_async(_setup())
    context["headers"] = _headers_docente()


@given("una actividad abierta ahora, visible a la comisión, que el segundo estudiante no rindió")
def actividad_abierta_visible_a_la_comision(context):
    async def _setup():
        async with SessionLocal() as session:
            store = SQLAlchemyEventStore(session)
            actividad_id = uuid4()
            await _actividad_abierta_creada(
                store, actividad_id, context["materia_id"], {context["comision_id"]}
            )
            await _evaluacion_finalizada(store, actividad_id, context["estudiante_1_id"], True)

    run_async(_setup())


@given("una comisión cuyos estudiantes nunca finalizaron ninguna Evaluacion")
def comision_sin_evaluaciones_finalizadas(context):
    async def _setup():
        async with SessionLocal() as session:
            materia_id = uuid4()
            comision, _estudiante_1, _estudiante_2 = await _comision_con_dos_estudiantes(
                session, materia_id
            )
            return materia_id, comision.id

    context["materia_id"], context["comision_id"] = run_async(_setup())
    context["headers"] = _headers_docente()


@given("una comisión de otra materia")
def comision_de_otra_materia(context):
    async def _setup():
        async with SessionLocal() as session:
            materia_id = uuid4()
            otra_materia_id = uuid4()
            comision, _estudiante = await _comision_con_un_estudiante(session, otra_materia_id)
            return materia_id, comision.id

    context["materia_id"], context["comision_id"] = run_async(_setup())
    context["headers"] = _headers_docente()


@given("una request sin JWT válido")
def request_sin_jwt(context):
    context["materia_id"], context["comision_id"] = uuid4(), uuid4()
    context["headers"] = None


@given("un Estudiante autenticado")
def estudiante_autenticado(context):
    context["materia_id"], context["comision_id"] = uuid4(), uuid4()
    context["headers"] = _headers_estudiante()


@given("una Evaluacion Finalizada de un Estudiante que no es quien hace la request")
def evaluacion_finalizada_de_estudiante_ajeno(context):
    async def _setup():
        async with SessionLocal() as session:
            materia_repo = SQLAlchemyMateriaRepository(session)
            banco_repo = SQLAlchemyBancoRepository(session)
            materia = Materia.crear(f"Ingeniería de Software {uuid.uuid4()}")
            await materia_repo.guardar(materia)
            banco = Banco.crear(materia.id)
            await banco_repo.guardar(banco)
            pregunta_id = await _pregunta_persistida(session, banco.id)

            _comision, estudiante = await _comision_con_un_estudiante(session, materia.id)
            store = SQLAlchemyEventStore(session)
            actividad_id = uuid4()
            await _actividad_cerrada_creada(store, actividad_id, materia.id)
            evaluacion_id = await _evaluacion_finalizada(
                store, actividad_id, estudiante.id, True, pregunta_id
            )
            return evaluacion_id

    context["evaluacion_id"] = run_async(_setup())
    context["headers"] = _headers_docente()


@given("una Evaluacion Finalizada de un Estudiante")
def evaluacion_finalizada_de_un_estudiante(context):
    evaluacion_finalizada_de_estudiante_ajeno(context)


def _get_desempeno_por_comision(context) -> None:
    async def _call():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(
                f"/analytics/materias/{context['materia_id']}/comisiones/{context['comision_id']}/desempeno",
                headers=context["headers"],
            )

    context["response"] = run_async(_call())


@when("un Docente hace GET /analytics/materias/X/comisiones/C1/desempeno")
def docente_hace_get_desempeno_comision(context):
    _get_desempeno_por_comision(context)


@when("un Docente consulta su desempeño")
def docente_consulta_desempeno(context):
    _get_desempeno_por_comision(context)


@when("un Docente hace GET /analytics/materias/X/comisiones/{esa comisión}/desempeno")
def docente_hace_get_con_comision_de_otra_materia(context):
    _get_desempeno_por_comision(context)


@when("hace GET /analytics/materias/X/comisiones/C1/desempeno")
def hace_get_desempeno_comision(context):
    _get_desempeno_por_comision(context)


@when("un Docente hace GET /evaluaciones/{id}/revision")
def docente_hace_get_revision(context):
    async def _call():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(
                f"/evaluaciones/{context['evaluacion_id']}/revision", headers=context["headers"]
            )

    context["response"] = run_async(_call())


@when("un Administrador hace GET /evaluaciones/{id}/revision")
def administrador_hace_get_revision(context):
    context["headers"] = _headers_administrador()

    async def _call():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(
                f"/evaluaciones/{context['evaluacion_id']}/revision", headers=context["headers"]
            )

    context["response"] = run_async(_call())


@then("recibe 200 con el primero mostrando su porcentaje acumulado y 0 pendientes")
def valida_primero_con_acumulado_y_sin_pendientes(context):
    response = context["response"]
    assert response.status_code == 200
    fila = next(f for f in response.json() if f["estudiante_id"] == str(context["estudiante_1_id"]))
    assert fila["porcentaje_aciertos_acumulado"] == 100.0
    assert fila["actividades_pendientes"] == 0


@then('el segundo aparece con "Sin datos" (null) y 1 actividad pendiente')
def valida_segundo_sin_datos_y_pendiente(context):
    response = context["response"]
    fila = next(f for f in response.json() if f["estudiante_id"] == str(context["estudiante_2_id"]))
    assert fila["porcentaje_aciertos_acumulado"] is None
    assert fila["actividades_pendientes"] == 1


@then('recibe 200 con todos los estudiantes en "Sin datos"')
def valida_200_todos_sin_datos(context):
    response = context["response"]
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(fila["porcentaje_aciertos_acumulado"] is None for fila in data)


@then("recibe 200 con el detalle completo, igual que si la pidiera el propio Estudiante")
def valida_200_detalle_completo(context):
    response = context["response"]
    assert response.status_code == 200
    cuerpo = response.json()
    assert cuerpo["cantidad_preguntas"] == 1
    assert cuerpo["cantidad_correctas"] == 1


@then("recibe 422")
def valida_422(context):
    assert context["response"].status_code == 422


@then("recibe 401")
def valida_401(context):
    assert context["response"].status_code == 401


@then("recibe 403")
def valida_403(context):
    assert context["response"].status_code == 403
