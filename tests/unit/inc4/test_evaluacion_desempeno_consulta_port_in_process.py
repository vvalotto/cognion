"""Tests unitarios de las funciones puras del adapter in-process (US-4.1.1, US-4.2.4, US-ADJ-44).

Sin sesión de BD — mismo criterio que `tests/unit/inc3/test_evaluacion_activa_query_repository.py`:
`EventoModel` se instancia directamente en memoria, sin persistir.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.actividad_evaluativa.entities.actividad_evaluativa_periodo_abierto import (
    ActividadEvaluativaPeriodoAbierto,
)
from src.actividad_evaluativa.frameworks.db.models import EventoModel
from src.analytics.entities.ports.evaluacion_desempeno_consulta_port import RespuestaVigente
from src.analytics.frameworks.adapters.evaluacion_desempeno_consulta_port_in_process import (
    _actividad_abierta_y_visible,
    _estados_por_estudiante,
    _respuestas_vigentes_de_stream,
    _resumen_de_stream,
)


def _evento(
    aggregate_id, event_type: str, payload: dict, sequence_number: int, occurred_at=None
) -> EventoModel:
    return EventoModel(
        aggregate_type="Evaluacion",
        aggregate_id=aggregate_id,
        sequence_number=sequence_number,
        event_type=event_type,
        payload=payload,
        occurred_at=occurred_at or datetime(2026, 1, 1, tzinfo=UTC),
    )


def _respuesta(pregunta_id, es_correcta: bool, sequence_number: int) -> EventoModel:
    return _evento(
        uuid4(),
        "RespuestaRegistrada",
        {"pregunta_id": str(pregunta_id), "es_correcta": es_correcta},
        sequence_number,
    )


class TestRespuestasVigentesDeStream:
    def test_sin_respuestas_devuelve_lista_vacia(self):
        eventos = [_evento(uuid4(), "EvaluacionIniciada", {"estudiante_id": str(uuid4())}, 1)]

        respuestas = _respuestas_vigentes_de_stream(eventos)

        assert respuestas == []

    def test_devuelve_una_fila_por_pregunta_sin_reintentos(self):
        estudiante_id = uuid4()
        pregunta_1, pregunta_2, pregunta_3 = uuid4(), uuid4(), uuid4()
        eventos = [
            _evento(uuid4(), "EvaluacionIniciada", {"estudiante_id": str(estudiante_id)}, 1),
            _respuesta(pregunta_1, True, 2),
            _respuesta(pregunta_2, False, 3),
            _respuesta(pregunta_3, True, 4),
        ]

        respuestas = _respuestas_vigentes_de_stream(eventos)

        assert {(r.pregunta_id, r.estudiante_id, r.es_correcta) for r in respuestas} == {
            (pregunta_1, estudiante_id, True),
            (pregunta_2, estudiante_id, False),
            (pregunta_3, estudiante_id, True),
        }

    def test_reintento_posterior_reemplaza_al_anterior(self):
        """Misma pregunta respondida dos veces: cuenta solo la más reciente (INV-AE-09)."""
        estudiante_id, pregunta_id = uuid4(), uuid4()
        eventos = [
            _evento(uuid4(), "EvaluacionIniciada", {"estudiante_id": str(estudiante_id)}, 1),
            _respuesta(pregunta_id, False, 2),
            _respuesta(pregunta_id, True, 3),
        ]

        respuestas = _respuestas_vigentes_de_stream(eventos)

        assert respuestas == [
            RespuestaVigente(pregunta_id=pregunta_id, estudiante_id=estudiante_id, es_correcta=True)
        ]

    def test_ignora_eventos_que_no_son_respuesta(self):
        estudiante_id, pregunta_id = uuid4(), uuid4()
        eventos = [
            _evento(uuid4(), "EvaluacionIniciada", {"estudiante_id": str(estudiante_id)}, 1),
            _respuesta(pregunta_id, True, 2),
            _evento(uuid4(), "EvaluacionFinalizada", {"actor": "estudiante"}, 3),
        ]

        respuestas = _respuestas_vigentes_de_stream(eventos)

        assert respuestas == [
            RespuestaVigente(pregunta_id=pregunta_id, estudiante_id=estudiante_id, es_correcta=True)
        ]


class TestResumenDeStream:
    def test_stream_sin_finalizada_devuelve_none(self):
        evaluacion_id, actividad_id, materia_id, estudiante_id = (
            uuid4(),
            uuid4(),
            uuid4(),
            uuid4(),
        )
        eventos = [
            EventoModel(
                aggregate_type="Evaluacion",
                aggregate_id=evaluacion_id,
                sequence_number=1,
                event_type="EvaluacionIniciada",
                payload={"actividad_id": str(actividad_id), "estudiante_id": str(estudiante_id)},
                occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
            )
        ]
        resumen = _resumen_de_stream(eventos, {actividad_id: materia_id})

        assert resumen is None

    def test_stream_finalizado_deriva_resumen_completo(self):
        evaluacion_id, actividad_id, materia_id, estudiante_id = (
            uuid4(),
            uuid4(),
            uuid4(),
            uuid4(),
        )
        pregunta_1, pregunta_2 = uuid4(), uuid4()
        finalizada_en = datetime(2026, 1, 2, tzinfo=UTC)
        eventos = [
            EventoModel(
                aggregate_type="Evaluacion",
                aggregate_id=evaluacion_id,
                sequence_number=1,
                event_type="EvaluacionIniciada",
                payload={"actividad_id": str(actividad_id), "estudiante_id": str(estudiante_id)},
                occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
            ),
            _respuesta(pregunta_1, True, 2),
            _respuesta(pregunta_2, False, 3),
            EventoModel(
                aggregate_type="Evaluacion",
                aggregate_id=evaluacion_id,
                sequence_number=4,
                event_type="EvaluacionFinalizada",
                payload={"actor": "estudiante"},
                occurred_at=finalizada_en,
            ),
        ]
        resumen = _resumen_de_stream(eventos, {actividad_id: materia_id})

        assert resumen is not None
        assert resumen.evaluacion_id == evaluacion_id
        assert resumen.actividad_id == actividad_id
        assert resumen.materia_id == materia_id
        assert resumen.finalizada_en == finalizada_en
        assert resumen.cantidad_correctas == 1
        assert resumen.cantidad_incorrectas == 1


def _actividad(
    fecha_apertura=None,
    fecha_cierre=None,
    cerrada_manualmente: bool = False,
    comisiones_ids=frozenset(),
) -> ActividadEvaluativaPeriodoAbierto:
    ahora = datetime(2026, 6, 15, 12, tzinfo=UTC)
    return ActividadEvaluativaPeriodoAbierto(
        id=uuid4(),
        materia_id=uuid4(),
        fecha_apertura=fecha_apertura or ahora - timedelta(days=1),
        fecha_cierre=fecha_cierre or ahora + timedelta(days=1),
        cantidad_preguntas=5,
        cantidad_intentos_permitidos=1,
        cerrada_manualmente=cerrada_manualmente,
        comisiones_ids=comisiones_ids,
    )


class TestActividadAbiertaYVisible:
    def test_actividad_vigente_sin_restriccion_de_comision_es_visible(self):
        ahora = datetime(2026, 6, 15, 12, tzinfo=UTC)
        actividad = _actividad()

        assert _actividad_abierta_y_visible(actividad, uuid4(), ahora) is True

    def test_actividad_cerrada_manualmente_no_es_visible(self):
        ahora = datetime(2026, 6, 15, 12, tzinfo=UTC)
        actividad = _actividad(cerrada_manualmente=True)

        assert _actividad_abierta_y_visible(actividad, uuid4(), ahora) is False

    def test_actividad_fuera_del_periodo_no_es_visible(self):
        ahora = datetime(2026, 6, 15, 12, tzinfo=UTC)
        actividad = _actividad(
            fecha_apertura=ahora - timedelta(days=10),
            fecha_cierre=ahora - timedelta(days=1),
        )

        assert _actividad_abierta_y_visible(actividad, uuid4(), ahora) is False

    def test_actividad_restringida_visible_a_su_comision(self):
        ahora = datetime(2026, 6, 15, 12, tzinfo=UTC)
        comision_id = uuid4()
        actividad = _actividad(comisiones_ids=frozenset({comision_id}))

        assert _actividad_abierta_y_visible(actividad, comision_id, ahora) is True

    def test_actividad_restringida_no_visible_a_otra_comision(self):
        ahora = datetime(2026, 6, 15, 12, tzinfo=UTC)
        actividad = _actividad(comisiones_ids=frozenset({uuid4()}))

        assert _actividad_abierta_y_visible(actividad, uuid4(), ahora) is False


def _stream_evaluacion(actividad_id, estudiante_id, eventos_siguientes: list | None = None):
    """Arma un stream mínimo de `Evaluacion` — `EvaluacionIniciada` + eventos adicionales."""
    iniciada = _evento(
        uuid4(),
        "EvaluacionIniciada",
        {
            "evaluacion_id": str(uuid4()),
            "actividad_id": str(actividad_id),
            "estudiante_id": str(estudiante_id),
            "ocurrido_en": datetime(2026, 1, 1, tzinfo=UTC).isoformat(),
            "preguntas_asignadas": [],
        },
        1,
    )
    return [iniciada, *(eventos_siguientes or [])]


class TestEstadosPorEstudiante:
    def test_estado_en_curso_por_defecto(self):
        actividad_id, estudiante_id = uuid4(), uuid4()
        streams = [_stream_evaluacion(actividad_id, estudiante_id)]

        estados = _estados_por_estudiante(streams, actividad_id, {str(estudiante_id)})

        assert estados == {estudiante_id: "en_curso"}

    def test_estado_finalizada(self):
        actividad_id, estudiante_id = uuid4(), uuid4()
        eventos_siguientes = [
            EventoModel(
                aggregate_type="Evaluacion",
                aggregate_id=uuid4(),
                sequence_number=2,
                event_type="EvaluacionFinalizada",
                payload={"actor": "estudiante"},
                occurred_at=datetime(2026, 1, 2, tzinfo=UTC),
            )
        ]
        streams = [_stream_evaluacion(actividad_id, estudiante_id, eventos_siguientes)]

        estados = _estados_por_estudiante(streams, actividad_id, {str(estudiante_id)})

        assert estados == {estudiante_id: "finalizada"}

    def test_ignora_streams_de_otra_actividad(self):
        actividad_id, otra_actividad_id, estudiante_id = uuid4(), uuid4(), uuid4()
        streams = [_stream_evaluacion(otra_actividad_id, estudiante_id)]

        estados = _estados_por_estudiante(streams, actividad_id, {str(estudiante_id)})

        assert estados == {}

    def test_ignora_estudiantes_fuera_del_filtro(self):
        actividad_id, estudiante_id = uuid4(), uuid4()
        streams = [_stream_evaluacion(actividad_id, estudiante_id)]

        estados = _estados_por_estudiante(streams, actividad_id, {str(uuid4())})

        assert estados == {}
