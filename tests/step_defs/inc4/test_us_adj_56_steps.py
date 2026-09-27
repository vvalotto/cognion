"""Steps BDD de US-ADJ-56 (`tests/features/inc6-adj/US-ADJ-56-desempeno-sesiones-en-vivo.feature`).

Escenarios en lenguaje de negocio ("abre 'Mi desempeño'") resueltos contra el endpoint HTTP real
— el frontend (sección "Sesiones en vivo" de `DesempenoResumenDetalle.tsx`) ya tiene su propia
cobertura en Vitest (Fase 4); acá se valida el contrato de datos que el backend le entrega.
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, scenarios, then, when
from sqlalchemy import text

from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.frameworks.adapters.proyecciones_en_vivo_repository import (
    SQLAlchemyProyeccionesEnVivo,
)
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

scenarios("../../features/inc6-adj/US-ADJ-56-desempeno-sesiones-en-vivo.feature")

AGGREGATE_TYPE_SESION = "ActividadEvaluativaEnVivo"
AGGREGATE_TYPE_PARTICIPACION = "ParticipacionEnVivo"
AGGREGATE_TYPE_EVALUACION = "Evaluacion"
AGGREGATE_TYPE_ACTIVIDAD = "ActividadEvaluativaPeriodoAbierto"


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM events"))
        await session.execute(text("DELETE FROM ranking_por_sesion"))
        await session.commit()


@pytest.fixture(autouse=True)
def limpiar_tablas():
    run_async(_limpiar_tablas())
    yield
    run_async(_limpiar_tablas())


@pytest.fixture
def context():
    return {"estudiante_id": uuid4(), "materia_id": uuid4()}


def _headers_estudiante(estudiante_id) -> dict[str, str]:
    jwt_vo = PyJWTIssuer().emitir(estudiante_id, TipoPerfil.ESTUDIANTE)
    return {"Authorization": f"Bearer {jwt_vo.token}"}


def _headers_docente() -> dict[str, str]:
    jwt_vo = PyJWTIssuer().emitir(uuid4(), TipoPerfil.DOCENTE)
    return {"Authorization": f"Bearer {jwt_vo.token}"}


async def _crear_estudiante_de_materia(session, materia_id) -> tuple[Usuario, Comision]:
    hasher = BcryptPasswordHasher()
    usuario_repo = SQLAlchemyUsuarioRepository(session)
    comision_repo = SQLAlchemyComisionRepository(session)

    admin = Usuario.crear(
        "Admin", f"admin.{uuid4()}@fiuner.edu.ar", hasher.hash("x"), TipoPerfil.ADMINISTRADOR
    )
    await usuario_repo.guardar(admin)
    comision = Comision.crear(materia_id, "Lunes 14-16hs", admin.id)
    await comision_repo.guardar(comision)

    estudiante = Usuario.crear_estudiante(
        "Estudiante", f"estudiante.{uuid4()}@fiuner.edu.ar", hasher.hash("x"), comision.id
    )
    await usuario_repo.guardar(estudiante)
    return estudiante, comision


async def _crear_sesion(store: SQLAlchemyEventStore, sesion_id, comision_id, materia_id) -> None:
    await store.append(
        AGGREGATE_TYPE_SESION,
        sesion_id,
        0,
        [
            EventoParaAlmacenar(
                "SesionEnVivoCreada",
                {
                    "sesion_id": str(sesion_id),
                    "comision_id": str(comision_id),
                    "materia_id": str(materia_id),
                    "preguntas": [{"pregunta_id": str(uuid4()), "orden": 0}],
                    "tiempo_limite_por_pregunta_segundos": 20,
                    "unidad_tematica": None,
                    "tema": None,
                },
            )
        ],
    )


async def _finalizar_sesion(store: SQLAlchemyEventStore, sesion_id, expected_seq: int) -> None:
    await store.append(
        AGGREGATE_TYPE_SESION,
        sesion_id,
        expected_seq,
        [EventoParaAlmacenar("SesionEnVivoFinalizada", {"sesion_id": str(sesion_id)})],
    )


async def _cancelar_sesion(store: SQLAlchemyEventStore, sesion_id, expected_seq: int) -> None:
    await store.append(
        AGGREGATE_TYPE_SESION,
        sesion_id,
        expected_seq,
        [EventoParaAlmacenar("SesionEnVivoCancelada", {"sesion_id": str(sesion_id)})],
    )


async def _unir(store: SQLAlchemyEventStore, sesion_id, estudiante_id) -> tuple[int, object]:
    participacion_id = uuid4()
    await store.append(
        AGGREGATE_TYPE_PARTICIPACION,
        participacion_id,
        0,
        [
            EventoParaAlmacenar(
                "EstudianteUnido",
                {
                    "sesion_id": str(sesion_id),
                    "estudiante_id": str(estudiante_id),
                    "unido_en": "2026-01-01T00:00:00+00:00",
                },
            )
        ],
    )
    return 1, participacion_id


async def _responder(
    store: SQLAlchemyEventStore,
    participacion_id,
    expected_seq: int,
    es_correcta: bool,
    puntaje: int,
) -> int:
    await store.append(
        AGGREGATE_TYPE_PARTICIPACION,
        participacion_id,
        expected_seq,
        [
            EventoParaAlmacenar(
                "RespuestaEnVivoRegistrada",
                {
                    "pregunta_id": str(uuid4()),
                    "contenido": {"opcion_indice": 0},
                    "es_correcta": es_correcta,
                    "tiempo_respuesta_segundos": 4.2,
                    "puntaje": puntaje,
                },
            )
        ],
    )
    return expected_seq + 1


async def _seed_ranking(session, sesion_id, estudiante_id, puntaje: int) -> None:
    proyecciones = SQLAlchemyProyeccionesEnVivo(session)
    await proyecciones.inicializar_participante(sesion_id, estudiante_id)
    if puntaje:
        await proyecciones.registrar_respuesta(sesion_id, estudiante_id, uuid4(), "0", puntaje)
    await session.commit()


async def _crear_actividad_periodo_abierto(
    store: SQLAlchemyEventStore, actividad_id, materia_id
) -> None:
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


async def _evaluacion_periodo_abierto_finalizada(
    store: SQLAlchemyEventStore, actividad_id, estudiante_id, correctas: int, incorrectas: int
) -> None:
    evaluacion_id = uuid4()
    seq = 1
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
    for correcta in [True] * correctas + [False] * incorrectas:
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
                        "es_correcta": correcta,
                    },
                )
            ],
        )
        seq += 1
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


def _get_mi_desempeno(context, materia_id=None) -> None:
    async def _call():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(
                f"/analytics/materias/{materia_id or context['materia_id']}/mi-desempeno",
                headers=_headers_estudiante(context["estudiante_id"]),
            )

    context["response"] = run_async(_call())


@given("un Estudiante que participó en dos sesiones en vivo finalizadas de su materia")
def estudiante_con_dos_sesiones_finalizadas(context):
    async def _setup():
        async with SessionLocal() as session:
            estudiante, comision = await _crear_estudiante_de_materia(
                session, context["materia_id"]
            )
            context["estudiante_id"] = estudiante.id
            store = SQLAlchemyEventStore(session)
            for _ in range(2):
                sesion_id = uuid4()
                await _crear_sesion(store, sesion_id, comision.id, context["materia_id"])
                seq, participacion_id = await _unir(store, sesion_id, estudiante.id)
                seq = await _responder(store, participacion_id, seq, True, 500)
                await _finalizar_sesion(store, sesion_id, expected_seq=1)
                await _seed_ranking(session, sesion_id, estudiante.id, 500)

    run_async(_setup())


@given("una sesión en la que el Estudiante quedó 3° de 14")
def sesion_con_posicion_3_de_14(context):
    async def _setup():
        async with SessionLocal() as session:
            estudiante, comision = await _crear_estudiante_de_materia(
                session, context["materia_id"]
            )
            context["estudiante_id"] = estudiante.id
            store = SQLAlchemyEventStore(session)
            sesion_id = uuid4()
            await _crear_sesion(store, sesion_id, comision.id, context["materia_id"])
            seq, participacion_id = await _unir(store, sesion_id, estudiante.id)
            await _responder(store, participacion_id, seq, True, 700)
            await _finalizar_sesion(store, sesion_id, expected_seq=1)
            # Ranking determinístico: 2 con más puntaje, el buscado 3°, 11 más abajo.
            await _seed_ranking(session, sesion_id, uuid4(), 950)
            await _seed_ranking(session, sesion_id, uuid4(), 900)
            await _seed_ranking(session, sesion_id, estudiante.id, 700)
            for _ in range(11):
                await _seed_ranking(session, sesion_id, uuid4(), 100)
            context["puntaje_esperado"] = 700

    run_async(_setup())


@given("una sesión en vivo todavía en curso")
def sesion_en_curso(context):
    async def _setup():
        async with SessionLocal() as session:
            estudiante, comision = await _crear_estudiante_de_materia(
                session, context["materia_id"]
            )
            context["estudiante_id"] = estudiante.id
            store = SQLAlchemyEventStore(session)
            sesion_id = uuid4()
            await _crear_sesion(store, sesion_id, comision.id, context["materia_id"])
            await _unir(store, sesion_id, estudiante.id)
            await _seed_ranking(session, sesion_id, estudiante.id, 0)

    run_async(_setup())


@given("una sesión en vivo cancelada antes de iniciar")
def sesion_cancelada(context):
    async def _setup():
        async with SessionLocal() as session:
            estudiante, comision = await _crear_estudiante_de_materia(
                session, context["materia_id"]
            )
            context["estudiante_id"] = estudiante.id
            store = SQLAlchemyEventStore(session)
            sesion_id = uuid4()
            await _crear_sesion(store, sesion_id, comision.id, context["materia_id"])
            await _unir(store, sesion_id, estudiante.id)
            await _cancelar_sesion(store, sesion_id, expected_seq=1)
            await _seed_ranking(session, sesion_id, estudiante.id, 0)

    run_async(_setup())


@given("un Estudiante que se unió a una sesión y no respondió ninguna pregunta")
def estudiante_se_unio_sin_responder(context):
    async def _setup():
        async with SessionLocal() as session:
            estudiante, comision = await _crear_estudiante_de_materia(
                session, context["materia_id"]
            )
            context["estudiante_id"] = estudiante.id
            store = SQLAlchemyEventStore(session)
            sesion_id = uuid4()
            await _crear_sesion(store, sesion_id, comision.id, context["materia_id"])
            await _unir(store, sesion_id, estudiante.id)
            await _finalizar_sesion(store, sesion_id, expected_seq=1)
            await _seed_ranking(session, sesion_id, estudiante.id, 0)

    run_async(_setup())


@given("un Estudiante con evaluaciones de período abierto y sesiones en vivo")
def estudiante_con_periodo_abierto_y_en_vivo(context):
    async def _setup():
        async with SessionLocal() as session:
            estudiante, comision = await _crear_estudiante_de_materia(
                session, context["materia_id"]
            )
            context["estudiante_id"] = estudiante.id
            store = SQLAlchemyEventStore(session)

            actividad_id = uuid4()
            await _crear_actividad_periodo_abierto(store, actividad_id, context["materia_id"])
            await _evaluacion_periodo_abierto_finalizada(store, actividad_id, estudiante.id, 8, 2)

            sesion_id = uuid4()
            await _crear_sesion(store, sesion_id, comision.id, context["materia_id"])
            seq, participacion_id = await _unir(store, sesion_id, estudiante.id)
            await _responder(store, participacion_id, seq, True, 400)
            await _finalizar_sesion(store, sesion_id, expected_seq=1)
            await _seed_ranking(session, sesion_id, estudiante.id, 400)

    run_async(_setup())


@given("un Estudiante que nunca participó en una sesión en vivo")
def estudiante_sin_sesiones_en_vivo(context):
    async def _setup():
        async with SessionLocal() as session:
            estudiante, _ = await _crear_estudiante_de_materia(session, context["materia_id"])
            context["estudiante_id"] = estudiante.id

    run_async(_setup())


@given('el Docente en "Desempeño por alumno" con un estudiante elegido')
def docente_con_estudiante_elegido(context):
    async def _setup():
        async with SessionLocal() as session:
            estudiante, comision = await _crear_estudiante_de_materia(
                session, context["materia_id"]
            )
            context["estudiante_id"] = estudiante.id
            store = SQLAlchemyEventStore(session)
            sesion_id = uuid4()
            await _crear_sesion(store, sesion_id, comision.id, context["materia_id"])
            seq, participacion_id = await _unir(store, sesion_id, estudiante.id)
            await _responder(store, participacion_id, seq, True, 600)
            await _finalizar_sesion(store, sesion_id, expected_seq=1)
            await _seed_ranking(session, sesion_id, estudiante.id, 600)

    run_async(_setup())


@given("un Estudiante con sesiones en vivo en dos materias")
def estudiante_con_sesiones_en_dos_materias(context):
    otra_materia_id = uuid4()

    async def _setup():
        async with SessionLocal() as session:
            estudiante, comision_x = await _crear_estudiante_de_materia(
                session, context["materia_id"]
            )
            context["estudiante_id"] = estudiante.id
            store = SQLAlchemyEventStore(session)

            sesion_x = uuid4()
            await _crear_sesion(store, sesion_x, comision_x.id, context["materia_id"])
            seq, participacion_id = await _unir(store, sesion_x, estudiante.id)
            await _responder(store, participacion_id, seq, True, 100)
            await _finalizar_sesion(store, sesion_x, expected_seq=1)
            await _seed_ranking(session, sesion_x, estudiante.id, 100)

            # El estudiante también participó de una sesión en otra materia — no debe mezclarse.
            hasher = BcryptPasswordHasher()
            comision_repo = SQLAlchemyComisionRepository(session)
            admin = Usuario.crear(
                "Admin2",
                f"admin2.{uuid4()}@fiuner.edu.ar",
                hasher.hash("x"),
                TipoPerfil.ADMINISTRADOR,
            )
            usuario_repo = SQLAlchemyUsuarioRepository(session)
            await usuario_repo.guardar(admin)
            comision_y = Comision.crear(otra_materia_id, "Martes 18-20hs", admin.id)
            await comision_repo.guardar(comision_y)

            sesion_y = uuid4()
            await _crear_sesion(store, sesion_y, comision_y.id, otra_materia_id)
            await _unir(store, sesion_y, estudiante.id)
            await _finalizar_sesion(store, sesion_y, expected_seq=1)
            await _seed_ranking(session, sesion_y, estudiante.id, 200)

    run_async(_setup())
    context["materia_y_id"] = otra_materia_id


@when('abre "Mi desempeño"')
def abre_mi_desempeno(context):
    _get_mi_desempeno(context)


@when("mira esa fila")
def mira_esa_fila(context):
    _get_mi_desempeno(context)


@when('el Estudiante abre "Mi desempeño"')
def el_estudiante_abre_mi_desempeno(context):
    _get_mi_desempeno(context)


@when("mira su desempeño")
def docente_mira_desempeno(context):
    async def _call():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(
                f"/analytics/materias/{context['materia_id']}/estudiantes/{context['estudiante_id']}/desempeno",
                headers=_headers_docente(),
            )

    context["response"] = run_async(_call())


@when("elige una materia")
def elige_una_materia(context):
    _get_mi_desempeno(context, materia_id=context["materia_id"])


@then("ve una fila por sesión con fecha, puntaje, posición, correctas e incorrectas")
def ve_una_fila_por_sesion(context):
    sesiones = context["response"].json()["sesiones_en_vivo"]
    assert len(sesiones) == 2
    for fila in sesiones:
        assert set(fila.keys()) >= {
            "sesion_id",
            "finalizada_en",
            "puntaje_final",
            "posicion",
            "cantidad_correctas",
            "cantidad_incorrectas",
        }


@then('dice "3° de 14" y el mismo puntaje que vio en el resultado final de la sesión')
def dice_posicion_3_de_14(context):
    fila = context["response"].json()["sesiones_en_vivo"][0]
    assert fila["posicion"] == 3
    assert fila["total_participantes"] == 14
    assert fila["puntaje_final"] == context["puntaje_esperado"]


@then("esa sesión no figura")
def esa_sesion_no_figura(context):
    assert context["response"].json()["sesiones_en_vivo"] == []


@then("la sesión figura con 0 puntos, 0 correctas y su posición")
def sesion_figura_en_cero(context):
    fila = context["response"].json()["sesiones_en_vivo"][0]
    assert fila["puntaje_final"] == 0
    assert fila["cantidad_correctas"] == 0
    assert fila["posicion"] == 1


@then("el resumen de período abierto es el mismo de antes")
def resumen_periodo_abierto_no_cambia(context):
    resumen = context["response"].json()["resumen"]
    assert resumen == {
        "total_correctas": 8,
        "total_incorrectas": 2,
        "porcentaje_acierto": 80,
        "cantidad_evaluaciones": 1,
    }


@then("las sesiones en vivo están en su propia sección")
def sesiones_en_vivo_en_propia_seccion(context):
    assert len(context["response"].json()["sesiones_en_vivo"]) == 1


@then('la sección dice "Todavía no participaste en sesiones en vivo"')
def seccion_vacia(context):
    """El texto literal lo verifica el frontend (Vitest) — acá se valida el dato: lista vacía."""
    assert context["response"].json()["sesiones_en_vivo"] == []


@then("ve la misma sección de sesiones en vivo de ese estudiante")
def docente_ve_sesiones_en_vivo_del_estudiante(context):
    sesiones = context["response"].json()["sesiones_en_vivo"]
    assert len(sesiones) == 1
    assert sesiones[0]["puntaje_final"] == 600


@then("solo ve las sesiones de esa materia")
def solo_ve_sesiones_de_esa_materia(context):
    sesiones = context["response"].json()["sesiones_en_vivo"]
    assert len(sesiones) == 1
    assert sesiones[0]["puntaje_final"] == 100
