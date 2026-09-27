"""Steps BDD de `US-ADJ-58` — cancelar, finalizar en cualquier etapa y no iniciar sin participantes.

Solo los escenarios `@backend`; los `@frontend` se validan con Vitest y los circuitos E2E de
`frontend/e2e/`.
"""

from __future__ import annotations

import asyncio
import uuid

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, parsers, scenario, then, when
from sqlalchemy import text

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
)
from src.actividad_evaluativa.frameworks.event_store.sqlalchemy_event_store import (
    SQLAlchemyEventStore,
)
from src.app import app
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import SessionLocal
from tests.integration.inc6._helpers import (
    crear_estudiante,
    headers_de,
    iniciar_sesion,
    mostrar_opciones,
    pregunta_actual_de,
    preparar_sesion,
    unirse_a_sesion,
)

FEATURE = "../../features/inc6-adj/US-ADJ-58-cancelar-finalizar-sesion.feature"

# El .feature mezcla escenarios backend y frontend: solo los backend se ejecutan con pytest-bdd
# (mismo criterio que `US-2.1.9`); los frontend se validan con Vitest y `frontend/e2e/`.


@scenario(FEATURE, "Cancelar una sesión en espera")
def test_cancelar_una_sesion_en_espera():
    """Escenario backend de US-ADJ-58."""


@scenario(FEATURE, "Los estudiantes en la sala se enteran de la cancelación")
def test_los_estudiantes_en_la_sala_se_enteran_de_la_cancelacion():
    """Escenario backend de US-ADJ-58."""


@scenario(FEATURE, "No se cancela una sesión iniciada")
def test_no_se_cancela_una_sesion_iniciada():
    """Escenario backend de US-ADJ-58."""


@scenario(FEATURE, "No se cancela dos veces")
def test_no_se_cancela_dos_veces():
    """Escenario backend de US-ADJ-58."""


@scenario(FEATURE, "Nadie se puede unir a una sesión cancelada")
def test_nadie_se_puede_unir_a_una_sesion_cancelada():
    """Escenario backend de US-ADJ-58."""


@scenario(FEATURE, "Cancelar una sesión inexistente")
def test_cancelar_una_sesion_inexistente():
    """Escenario backend de US-ADJ-58."""


@scenario(FEATURE, "Solo el Docente cancela")
def test_solo_el_docente_cancela():
    """Escenario backend de US-ADJ-58."""


@scenario(FEATURE, "No se inicia sin participantes")
def test_no_se_inicia_sin_participantes():
    """Escenario backend de US-ADJ-58."""


@scenario(FEATURE, "Con un participante se inicia")
def test_con_un_participante_se_inicia():
    """Escenario backend de US-ADJ-58."""


@scenario(FEATURE, "Finalizar con la pregunta sin opciones mostradas")
def test_finalizar_con_la_pregunta_sin_opciones_mostradas():
    """Escenario backend de US-ADJ-58."""


@scenario(FEATURE, "Finalizar con las opciones a la vista")
def test_finalizar_con_las_opciones_a_la_vista():
    """Escenario backend de US-ADJ-58."""


# Opción múltiple de `preparar_sesion`: "A" a "D", la "B" (índice 1) correcta.
CORRECTA = {"opcion_indice": 1}


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM events"))
        await session.execute(text("DELETE FROM ranking_por_sesion"))
        await session.execute(text("DELETE FROM distribucion_por_pregunta"))
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


def _docente() -> dict[str, str]:
    return headers_de(uuid.uuid4(), TipoPerfil.DOCENTE)


async def _post(sesion_id: str, accion: str, headers: dict[str, str], json=None):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(
            f"/sesiones-en-vivo/{sesion_id}/{accion}", headers=headers, json=json
        )


async def _reconstruir(sesion_id: str) -> tuple[ActividadEvaluativaEnVivo, list]:
    async with SessionLocal() as session:
        eventos = await SQLAlchemyEventStore(session).load(
            "ActividadEvaluativaEnVivo", uuid.UUID(sesion_id)
        )
    return ActividadEvaluativaEnVivo.reconstruir(eventos), eventos


async def _en_espera(context, unidos: int) -> None:
    sesion_id, comision_id = await preparar_sesion(opcion_multiple=True)
    estudiantes = [await crear_estudiante(comision_id) for _ in range(unidos + 1)]
    for _, headers in estudiantes[:unidos]:
        await unirse_a_sesion(sesion_id, headers)
    context.update(
        sesion_id=sesion_id,
        comision_id=comision_id,
        unidos=[headers for _, headers in estudiantes[:unidos]],
        headers_estudiante=estudiantes[-1][1],
    )


# --- Given ---


@given("una sesión en vivo EnEspera")
def sesion_en_espera(context):
    run_async(_en_espera(context, unidos=0))


@given("una sesión en vivo EnEspera con dos Estudiantes unidos")
def sesion_con_dos_unidos(context):
    run_async(_en_espera(context, unidos=2))


@given("una sesión en vivo EnEspera sin Estudiantes unidos")
def sesion_sin_unidos(context):
    run_async(_en_espera(context, unidos=0))


@given("una sesión en vivo EnEspera con un Estudiante unido")
def sesion_con_un_unido(context):
    run_async(_en_espera(context, unidos=1))


@given("una sesión en vivo EnCurso")
def sesion_en_curso(context):
    run_async(_en_espera(context, unidos=0))
    run_async(iniciar_sesion(context["sesion_id"]))


@given("una sesión en vivo Cancelada")
def sesion_cancelada(context):
    run_async(_en_espera(context, unidos=0))
    assert run_async(_post(context["sesion_id"], "cancelar", _docente())).status_code == 200
    context["eventos_antes"] = len(run_async(_reconstruir(context["sesion_id"]))[1])


@given("un sesion_id que no corresponde a ninguna sesión")
def sesion_inexistente(context):
    context["sesion_id"] = str(uuid.uuid4())


@given("un usuario autenticado con rol Estudiante")
def usuario_estudiante(context):
    run_async(_en_espera(context, unidos=0))


@given("una sesión EnCurso en la pregunta 1 de 4, sin opciones mostradas")
def en_curso_sin_opciones(context):
    async def _armar() -> None:
        sesion_id, comision_id = await preparar_sesion(cantidad_preguntas=4, opcion_multiple=True)
        _, headers = await crear_estudiante(comision_id)
        await unirse_a_sesion(sesion_id, headers)
        await iniciar_sesion(sesion_id)
        context.update(sesion_id=sesion_id, headers_estudiante=headers)

    run_async(_armar())


@given("una sesión EnCurso con las opciones mostradas y dos respuestas registradas")
def en_curso_con_dos_respuestas(context):
    async def _armar() -> None:
        sesion_id, comision_id = await preparar_sesion(opcion_multiple=True)
        estudiantes = [await crear_estudiante(comision_id) for _ in range(2)]
        for _, headers in estudiantes:
            await unirse_a_sesion(sesion_id, headers)
        await iniciar_sesion(sesion_id)
        await mostrar_opciones(sesion_id)
        pregunta_id = await pregunta_actual_de(sesion_id)
        for _, headers in estudiantes:
            respuesta = await _post(
                sesion_id,
                "responder",
                headers,
                json={"pregunta_id": pregunta_id, "contenido": CORRECTA},
            )
            assert respuesta.status_code == 200, respuesta.text
        context.update(
            sesion_id=sesion_id,
            headers_estudiante=estudiantes[0][1],
            respondieron=[estudiante_id for estudiante_id, _ in estudiantes],
        )

    run_async(_armar())


# --- When ---


def _con_conectados(context, accion: str, headers_conectados: list[dict[str, str]]) -> None:
    """Ejecuta `accion` como Docente con `headers_conectados` escuchando el canal."""
    docente = _docente()
    sesion_id = context["sesion_id"]
    tokens = [h["Authorization"].split()[1] for h in headers_conectados]
    with TestClient(app) as client:
        sockets = [
            client.websocket_connect(f"/sesiones-en-vivo/{sesion_id}/canal?token={token}")
            for token in tokens
        ]
        conectados = [ws.__enter__() for ws in sockets]
        try:
            context["response"] = client.post(
                f"/sesiones-en-vivo/{sesion_id}/{accion}", headers=docente
            )
            if context["response"].status_code == 200:
                context["mensajes"] = [ws.receive_json() for ws in conectados]
        finally:
            for ws in sockets:
                ws.__exit__(None, None, None)


@when("el Docente cancela la sesión")
def docente_cancela(context):
    _con_conectados(context, "cancelar", context["unidos"])


@when("el Docente intenta cancelar la sesión")
def docente_intenta_cancelar(context):
    context["response"] = run_async(_post(context["sesion_id"], "cancelar", _docente()))


@when("un Estudiante intenta unirse")
def estudiante_intenta_unirse(context):
    context["response"] = run_async(
        _post(context["sesion_id"], "unirse", context["headers_estudiante"])
    )


@when("intenta cancelar la sesión")
def estudiante_intenta_cancelar(context):
    context["response"] = run_async(
        _post(context["sesion_id"], "cancelar", context["headers_estudiante"])
    )


@when("el Docente intenta iniciar la sesión")
@when("el Docente inicia la sesión")
def docente_inicia(context):
    context["response"] = run_async(_post(context["sesion_id"], "iniciar", _docente()))


@when("el Docente finaliza la sesión")
def docente_finaliza(context):
    _con_conectados(context, "finalizar", [context["headers_estudiante"]])


# --- Then ---


@then("la sesión queda Cancelada")
def queda_cancelada(context):
    assert context["response"].status_code == 200
    assert context["response"].json()["estado"] == "Cancelada"
    sesion, eventos = run_async(_reconstruir(context["sesion_id"]))
    assert sesion.estado == "Cancelada"
    assert eventos[-1].event_type == "SesionEnVivoCancelada"


@then("deja de figurar en el listado de sesiones EnEspera y EnCurso de la Comisión")
def no_figura_en_el_listado(context):
    async def _listar():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.get(
                "/sesiones-en-vivo",
                params={"comision_id": context["comision_id"]},
                headers=_docente(),
            )

    respuesta = run_async(_listar())
    assert respuesta.status_code == 200
    assert context["sesion_id"] not in [s["id"] for s in respuesta.json()]


@then("todos los conectados reciben el mensaje sesion_cancelada")
def reciben_sesion_cancelada(context):
    assert context["mensajes"] == [{"tipo": "sesion_cancelada"}] * 2


@then(parsers.parse("el sistema rechaza con SesionYaIniciada ({codigo:d})"))
def rechazo_ya_iniciada(context, codigo):
    assert context["response"].status_code == codigo
    assert "iniciada" in context["response"].json()["detail"]


@then("la sesión sigue EnCurso")
def sigue_en_curso(context):
    sesion, _ = run_async(_reconstruir(context["sesion_id"]))
    assert sesion.estado == "EnCurso"


@then(parsers.parse("el sistema rechaza con SesionYaCancelada ({codigo:d}) sin emitir otro evento"))
def rechazo_ya_cancelada_sin_evento(context, codigo):
    assert context["response"].status_code == codigo
    assert "cancelada" in context["response"].json()["detail"]
    _, eventos = run_async(_reconstruir(context["sesion_id"]))
    assert len(eventos) == context["eventos_antes"]


@then(parsers.parse("el sistema rechaza con SesionYaCancelada ({codigo:d})"))
def rechazo_ya_cancelada(context, codigo):
    assert context["response"].status_code == codigo
    assert "cancelada" in context["response"].json()["detail"]


@then(parsers.parse("el sistema rechaza con SesionNoExiste ({codigo:d})"))
def rechazo_inexistente(context, codigo):
    assert context["response"].status_code == codigo


@then(parsers.parse("el sistema responde {codigo:d}"))
def sistema_responde(context, codigo):
    assert context["response"].status_code == codigo


@then(parsers.parse("el sistema rechaza con SinParticipantes ({codigo:d})"))
def rechazo_sin_participantes(context, codigo):
    assert context["response"].status_code == codigo
    assert "no tiene participantes" in context["response"].json()["detail"]


@then("la sesión sigue EnEspera")
def sigue_en_espera(context):
    sesion, eventos = run_async(_reconstruir(context["sesion_id"]))
    assert sesion.estado == "EnEspera"
    assert len(eventos) == 1


@then("la sesión pasa a EnCurso")
def pasa_a_en_curso(context):
    assert context["response"].status_code == 200
    assert context["response"].json()["estado"] == "EnCurso"


@then("la sesión queda Finalizada")
def queda_finalizada(context):
    assert context["response"].status_code == 200
    sesion, _ = run_async(_reconstruir(context["sesion_id"]))
    assert sesion.estado == "Finalizada"


@then("todos los conectados reciben el ranking final")
def reciben_ranking_final(context):
    assert context["mensajes"][0]["tipo"] == "sesion_finalizada"


@then("el ranking final incluye el puntaje de esas dos respuestas")
def ranking_incluye_respuestas(context):
    ranking = context["mensajes"][0]["ranking"]
    por_estudiante = {fila["estudiante_id"]: fila["puntaje_acumulado"] for fila in ranking}
    assert all(por_estudiante[estudiante_id] > 0 for estudiante_id in context["respondieron"])


@then("la pregunta actual no se cerró (no se emite PreguntaEnVivoCerrada)")
def pregunta_no_cerrada(context):
    _, eventos = run_async(_reconstruir(context["sesion_id"]))
    assert "PreguntaEnVivoCerrada" not in [e.event_type for e in eventos]
