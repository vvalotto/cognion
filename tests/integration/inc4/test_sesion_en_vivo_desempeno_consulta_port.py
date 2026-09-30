"""Tests de integración de `SesionEnVivoDesempenoConsultaPortInProcess` (US-ADJ-56).

Escribe eventos reales en la tabla `events` (streams `ActividadEvaluativaEnVivo` y
`ParticipacionEnVivo`, vía `SQLAlchemyEventStore`) y filas reales en `ranking_por_sesion` (vía
`SQLAlchemyProyeccionesEnVivo`, el mismo adapter de escritura que usa el modo en vivo) — mismo
criterio que `tests/integration/inc4/test_evaluacion_desempeno_consulta_port.py`.
"""

from __future__ import annotations

from uuid import uuid4

from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.frameworks.adapters.proyecciones_en_vivo_repository import (
    SQLAlchemyProyeccionesEnVivo,
)
from src.actividad_evaluativa.frameworks.event_store.sqlalchemy_event_store import (
    SQLAlchemyEventStore,
)
from src.analytics.frameworks.adapters.sesion_en_vivo_desempeno_consulta_port_in_process import (
    SesionEnVivoDesempenoConsultaPortInProcess,
)

AGGREGATE_TYPE_SESION = "ActividadEvaluativaEnVivo"
AGGREGATE_TYPE_PARTICIPACION = "ParticipacionEnVivo"


async def _crear_sesion(
    store: SQLAlchemyEventStore, sesion_id, comision_id, materia_id, cantidad_preguntas: int = 5
) -> None:
    preguntas = [{"pregunta_id": str(uuid4()), "orden": i} for i in range(cantidad_preguntas)]
    await store.append(
        AGGREGATE_TYPE_SESION,
        sesion_id,
        0,
        [
            EventoParaAlmacenar(
                event_type="SesionEnVivoCreada",
                payload={
                    "sesion_id": str(sesion_id),
                    "comision_id": str(comision_id),
                    "materia_id": str(materia_id),
                    "preguntas": preguntas,
                    "tiempo_limite_por_pregunta_segundos": 20,
                    "unidad_tematica": None,
                    "tema": None,
                },
            )
        ],
    )


async def _finalizar_sesion(store: SQLAlchemyEventStore, sesion_id, expected_seq: int) -> int:
    await store.append(
        AGGREGATE_TYPE_SESION,
        sesion_id,
        expected_seq,
        [
            EventoParaAlmacenar(
                event_type="SesionEnVivoFinalizada",
                payload={"sesion_id": str(sesion_id)},
            )
        ],
    )
    return expected_seq + 1


async def _cancelar_sesion(store: SQLAlchemyEventStore, sesion_id, expected_seq: int) -> None:
    await store.append(
        AGGREGATE_TYPE_SESION,
        sesion_id,
        expected_seq,
        [
            EventoParaAlmacenar(
                event_type="SesionEnVivoCancelada",
                payload={"sesion_id": str(sesion_id)},
            )
        ],
    )


async def _unir_estudiante(
    store: SQLAlchemyEventStore, sesion_id, estudiante_id, participacion_id=None
) -> int:
    await store.append(
        AGGREGATE_TYPE_PARTICIPACION,
        participacion_id or uuid4(),
        0,
        [
            EventoParaAlmacenar(
                event_type="EstudianteUnido",
                payload={
                    "sesion_id": str(sesion_id),
                    "estudiante_id": str(estudiante_id),
                    "unido_en": "2026-01-01T00:00:00+00:00",
                },
            )
        ],
    )
    return 1


async def _responder(
    store: SQLAlchemyEventStore,
    participacion_id,
    expected_seq: int,
    pregunta_id,
    es_correcta: bool,
    puntaje: int,
) -> int:
    await store.append(
        AGGREGATE_TYPE_PARTICIPACION,
        participacion_id,
        expected_seq,
        [
            EventoParaAlmacenar(
                event_type="RespuestaEnVivoRegistrada",
                payload={
                    "pregunta_id": str(pregunta_id),
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
    """Inicializa y suma puntaje al participante en `ranking_por_sesion` (mismo adapter real)."""
    proyecciones = SQLAlchemyProyeccionesEnVivo(session)
    await proyecciones.inicializar_participante(sesion_id, estudiante_id)
    if puntaje:
        await proyecciones.registrar_respuesta(sesion_id, estudiante_id, uuid4(), "0", puntaje)
    await session.commit()


class TestListarSesionesFinalizadas:
    async def test_sesion_finalizada_con_respuestas_aparece_con_todos_los_datos(self, session):
        store = SQLAlchemyEventStore(session)
        adapter = SesionEnVivoDesempenoConsultaPortInProcess(session)
        sesion_id, comision_id, materia_id, estudiante_id = uuid4(), uuid4(), uuid4(), uuid4()
        participacion_id = uuid4()

        await _crear_sesion(store, sesion_id, comision_id, materia_id, cantidad_preguntas=10)
        seq = await _unir_estudiante(store, sesion_id, estudiante_id, participacion_id)
        seq = await _responder(store, participacion_id, seq, uuid4(), True, 500)
        seq = await _responder(store, participacion_id, seq, uuid4(), False, 0)
        seq = await _responder(store, participacion_id, seq, uuid4(), True, 300)
        await _finalizar_sesion(store, sesion_id, expected_seq=1)
        await _seed_ranking(session, sesion_id, estudiante_id, 800)

        resultado = await adapter.listar_sesiones_finalizadas(estudiante_id, materia_id)

        assert len(resultado) == 1
        fila = resultado[0]
        assert fila.sesion_id == sesion_id
        assert fila.comision_id == comision_id
        assert fila.materia_id == materia_id
        assert fila.cantidad_preguntas == 10
        assert fila.cantidad_correctas == 2
        assert fila.cantidad_incorrectas == 1
        assert fila.puntaje_final == 800
        assert fila.posicion == 1
        assert fila.total_participantes == 1

    async def test_sesion_no_finalizada_no_aparece(self, session):
        store = SQLAlchemyEventStore(session)
        adapter = SesionEnVivoDesempenoConsultaPortInProcess(session)
        sesion_id, materia_id, estudiante_id = uuid4(), uuid4(), uuid4()

        await _crear_sesion(store, sesion_id, uuid4(), materia_id)
        await _unir_estudiante(store, sesion_id, estudiante_id)
        await _seed_ranking(session, sesion_id, estudiante_id, 0)

        resultado = await adapter.listar_sesiones_finalizadas(estudiante_id, materia_id)

        assert resultado == []

    async def test_sesion_cancelada_no_aparece(self, session):
        store = SQLAlchemyEventStore(session)
        adapter = SesionEnVivoDesempenoConsultaPortInProcess(session)
        sesion_id, materia_id, estudiante_id = uuid4(), uuid4(), uuid4()

        await _crear_sesion(store, sesion_id, uuid4(), materia_id)
        await _unir_estudiante(store, sesion_id, estudiante_id)
        await _cancelar_sesion(store, sesion_id, expected_seq=1)
        await _seed_ranking(session, sesion_id, estudiante_id, 0)

        resultado = await adapter.listar_sesiones_finalizadas(estudiante_id, materia_id)

        assert resultado == []

    async def test_se_unio_pero_no_respondio_aparece_en_cero(self, session):
        store = SQLAlchemyEventStore(session)
        adapter = SesionEnVivoDesempenoConsultaPortInProcess(session)
        sesion_id, materia_id, estudiante_id = uuid4(), uuid4(), uuid4()

        await _crear_sesion(store, sesion_id, uuid4(), materia_id)
        await _unir_estudiante(store, sesion_id, estudiante_id)
        await _finalizar_sesion(store, sesion_id, expected_seq=1)
        await _seed_ranking(session, sesion_id, estudiante_id, 0)

        resultado = await adapter.listar_sesiones_finalizadas(estudiante_id, materia_id)

        assert len(resultado) == 1
        assert resultado[0].cantidad_correctas == 0
        assert resultado[0].cantidad_incorrectas == 0
        assert resultado[0].puntaje_final == 0
        assert resultado[0].posicion == 1

    async def test_filtro_por_materia_excluye_otras_materias(self, session):
        store = SQLAlchemyEventStore(session)
        adapter = SesionEnVivoDesempenoConsultaPortInProcess(session)
        estudiante_id = uuid4()
        materia_x, materia_y = uuid4(), uuid4()
        sesion_x, sesion_y = uuid4(), uuid4()

        await _crear_sesion(store, sesion_x, uuid4(), materia_x)
        await _unir_estudiante(store, sesion_x, estudiante_id)
        await _finalizar_sesion(store, sesion_x, expected_seq=1)
        await _seed_ranking(session, sesion_x, estudiante_id, 100)

        await _crear_sesion(store, sesion_y, uuid4(), materia_y)
        await _unir_estudiante(store, sesion_y, estudiante_id)
        await _finalizar_sesion(store, sesion_y, expected_seq=1)
        await _seed_ranking(session, sesion_y, estudiante_id, 200)

        resultado = await adapter.listar_sesiones_finalizadas(estudiante_id, materia_x)

        assert [fila.sesion_id for fila in resultado] == [sesion_x]

    async def test_sin_materia_id_trae_de_todas_las_materias(self, session):
        store = SQLAlchemyEventStore(session)
        adapter = SesionEnVivoDesempenoConsultaPortInProcess(session)
        estudiante_id = uuid4()
        sesion_x, sesion_y = uuid4(), uuid4()

        await _crear_sesion(store, sesion_x, uuid4(), uuid4())
        await _unir_estudiante(store, sesion_x, estudiante_id)
        await _finalizar_sesion(store, sesion_x, expected_seq=1)
        await _seed_ranking(session, sesion_x, estudiante_id, 100)

        await _crear_sesion(store, sesion_y, uuid4(), uuid4())
        await _unir_estudiante(store, sesion_y, estudiante_id)
        await _finalizar_sesion(store, sesion_y, expected_seq=1)
        await _seed_ranking(session, sesion_y, estudiante_id, 200)

        resultado = await adapter.listar_sesiones_finalizadas(estudiante_id, None)

        assert {fila.sesion_id for fila in resultado} == {sesion_x, sesion_y}

    async def test_posicion_y_total_participantes_reflejan_a_todos_los_participantes(self, session):
        store = SQLAlchemyEventStore(session)
        adapter = SesionEnVivoDesempenoConsultaPortInProcess(session)
        sesion_id, materia_id = uuid4(), uuid4()
        lider, buscado, ultimo = uuid4(), uuid4(), uuid4()

        await _crear_sesion(store, sesion_id, uuid4(), materia_id)
        await _unir_estudiante(store, sesion_id, lider)
        await _unir_estudiante(store, sesion_id, buscado)
        await _unir_estudiante(store, sesion_id, ultimo)
        await _finalizar_sesion(store, sesion_id, expected_seq=1)
        await _seed_ranking(session, sesion_id, lider, 900)
        await _seed_ranking(session, sesion_id, buscado, 500)
        await _seed_ranking(session, sesion_id, ultimo, 100)

        resultado = await adapter.listar_sesiones_finalizadas(buscado, materia_id)

        assert len(resultado) == 1
        assert resultado[0].posicion == 2
        assert resultado[0].total_participantes == 3

    async def test_estudiante_sin_participaciones_devuelve_lista_vacia(self, session):
        adapter = SesionEnVivoDesempenoConsultaPortInProcess(session)

        resultado = await adapter.listar_sesiones_finalizadas(uuid4(), uuid4())

        assert resultado == []
