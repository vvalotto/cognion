"""Tests de integración de `EvaluacionDesempenoConsultaPortInProcess` (US-4.1.1).

Escribe eventos reales en la tabla `events` (vía `SQLAlchemyEventStore`, mismo event store
que usa Actividad Evaluativa) y ejercita el algoritmo completo del adapter contra Postgres —
mismos 5 escenarios que `tests/features/inc4/US-4.1.1-infra-consulta-analytics.feature`.
"""

from __future__ import annotations

from uuid import uuid4

from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.frameworks.event_store.sqlalchemy_event_store import (
    SQLAlchemyEventStore,
)
from src.analytics.frameworks.adapters.evaluacion_desempeno_consulta_port_in_process import (
    EvaluacionDesempenoConsultaPortInProcess,
)

AGGREGATE_TYPE_EVALUACION = "Evaluacion"
AGGREGATE_TYPE_ACTIVIDAD = "ActividadEvaluativaPeriodoAbierto"


async def _crear_actividad(store: SQLAlchemyEventStore, actividad_id, materia_id) -> None:
    await store.append(
        AGGREGATE_TYPE_ACTIVIDAD,
        actividad_id,
        0,
        [
            EventoParaAlmacenar(
                event_type="ActividadEvaluativaCreada",
                payload={"actividad_id": str(actividad_id), "materia_id": str(materia_id)},
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
                event_type="EvaluacionIniciada",
                payload={
                    "evaluacion_id": str(evaluacion_id),
                    "actividad_id": str(actividad_id),
                    "estudiante_id": str(estudiante_id),
                },
            )
        ],
    )
    return 1


async def _registrar_respuesta(
    store: SQLAlchemyEventStore,
    evaluacion_id,
    expected_seq: int,
    pregunta_id,
    es_correcta: bool,
    numero_intento: int = 1,
) -> int:
    await store.append(
        AGGREGATE_TYPE_EVALUACION,
        evaluacion_id,
        expected_seq,
        [
            EventoParaAlmacenar(
                event_type="RespuestaRegistrada",
                payload={
                    "respuesta_id": str(uuid4()),
                    "evaluacion_id": str(evaluacion_id),
                    "pregunta_id": str(pregunta_id),
                    "numero_intento": numero_intento,
                    "contenido": {},
                    "es_correcta": es_correcta,
                },
            )
        ],
    )
    return expected_seq + 1


async def _finalizar_evaluacion(
    store: SQLAlchemyEventStore, evaluacion_id, expected_seq: int, actor: str = "estudiante"
) -> int:
    await store.append(
        AGGREGATE_TYPE_EVALUACION,
        evaluacion_id,
        expected_seq,
        [
            EventoParaAlmacenar(
                event_type="EvaluacionFinalizada",
                payload={"evaluacion_id": str(evaluacion_id), "actor": actor},
            )
        ],
    )
    return expected_seq + 1


class TestListarEvaluacionesFinalizadas:
    async def test_estudiante_con_evaluaciones_finalizadas_en_la_materia(self, session):
        store = SQLAlchemyEventStore(session)
        adapter = EvaluacionDesempenoConsultaPortInProcess(session)
        estudiante_id, materia_id, actividad_id = uuid4(), uuid4(), uuid4()
        await _crear_actividad(store, actividad_id, materia_id)

        evaluacion_1 = uuid4()
        seq = await _iniciar_evaluacion(store, evaluacion_1, actividad_id, estudiante_id)
        for _ in range(8):
            seq = await _registrar_respuesta(store, evaluacion_1, seq, uuid4(), True)
        for _ in range(2):
            seq = await _registrar_respuesta(store, evaluacion_1, seq, uuid4(), False)
        await _finalizar_evaluacion(store, evaluacion_1, seq)

        evaluacion_2 = uuid4()
        seq = await _iniciar_evaluacion(store, evaluacion_2, actividad_id, estudiante_id)
        for _ in range(5):
            seq = await _registrar_respuesta(store, evaluacion_2, seq, uuid4(), True)
        for _ in range(3):
            seq = await _registrar_respuesta(store, evaluacion_2, seq, uuid4(), False)
        await _finalizar_evaluacion(store, evaluacion_2, seq)

        resultado = await adapter.listar_evaluaciones_finalizadas(estudiante_id, materia_id)

        assert len(resultado) == 2
        por_id = {r.evaluacion_id: r for r in resultado}
        assert (
            por_id[evaluacion_1].cantidad_correctas,
            por_id[evaluacion_1].cantidad_incorrectas,
        ) == (
            8,
            2,
        )
        assert (
            por_id[evaluacion_2].cantidad_correctas,
            por_id[evaluacion_2].cantidad_incorrectas,
        ) == (
            5,
            3,
        )

    async def test_evaluacion_en_curso_sin_finalizar_no_aparece(self, session):
        store = SQLAlchemyEventStore(session)
        adapter = EvaluacionDesempenoConsultaPortInProcess(session)
        estudiante_id, materia_id, actividad_id = uuid4(), uuid4(), uuid4()
        await _crear_actividad(store, actividad_id, materia_id)

        evaluacion_id = uuid4()
        seq = await _iniciar_evaluacion(store, evaluacion_id, actividad_id, estudiante_id)
        await _registrar_respuesta(store, evaluacion_id, seq, uuid4(), True)

        resultado = await adapter.listar_evaluaciones_finalizadas(estudiante_id, materia_id)

        assert resultado == []

    async def test_reintento_cuenta_solo_la_respuesta_vigente(self, session):
        store = SQLAlchemyEventStore(session)
        adapter = EvaluacionDesempenoConsultaPortInProcess(session)
        estudiante_id, materia_id, actividad_id = uuid4(), uuid4(), uuid4()
        await _crear_actividad(store, actividad_id, materia_id)

        evaluacion_id, pregunta_id = uuid4(), uuid4()
        seq = await _iniciar_evaluacion(store, evaluacion_id, actividad_id, estudiante_id)
        seq = await _registrar_respuesta(
            store, evaluacion_id, seq, pregunta_id, False, numero_intento=1
        )
        seq = await _registrar_respuesta(
            store, evaluacion_id, seq, pregunta_id, True, numero_intento=2
        )
        await _finalizar_evaluacion(store, evaluacion_id, seq)

        resultado = await adapter.listar_evaluaciones_finalizadas(estudiante_id, materia_id)

        assert len(resultado) == 1
        assert (resultado[0].cantidad_correctas, resultado[0].cantidad_incorrectas) == (1, 0)

    async def test_filtro_por_materia_excluye_otras_materias(self, session):
        store = SQLAlchemyEventStore(session)
        adapter = EvaluacionDesempenoConsultaPortInProcess(session)
        estudiante_id = uuid4()
        materia_x, materia_y = uuid4(), uuid4()
        actividad_x, actividad_y = uuid4(), uuid4()
        await _crear_actividad(store, actividad_x, materia_x)
        await _crear_actividad(store, actividad_y, materia_y)

        evaluacion_x = uuid4()
        seq = await _iniciar_evaluacion(store, evaluacion_x, actividad_x, estudiante_id)
        await _finalizar_evaluacion(store, evaluacion_x, seq)

        evaluacion_y = uuid4()
        seq = await _iniciar_evaluacion(store, evaluacion_y, actividad_y, estudiante_id)
        await _finalizar_evaluacion(store, evaluacion_y, seq)

        resultado = await adapter.listar_evaluaciones_finalizadas(estudiante_id, materia_x)

        assert [r.evaluacion_id for r in resultado] == [evaluacion_x]

    async def test_estudiante_sin_evaluaciones_finalizadas_devuelve_lista_vacia(self, session):
        adapter = EvaluacionDesempenoConsultaPortInProcess(session)

        resultado = await adapter.listar_evaluaciones_finalizadas(uuid4(), uuid4())

        assert resultado == []
