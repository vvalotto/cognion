from datetime import UTC, datetime
from uuid import uuid4

from src.actividad_evaluativa.entities.evaluacion import EstadoEvaluacion
from src.actividad_evaluativa.frameworks.adapters.evaluacion_activa_query_repository import (
    _resumen_de_stream,
)
from src.actividad_evaluativa.frameworks.db.models import EventoModel


def _evento(
    aggregate_id, event_type: str, payload: dict, occurred_at: datetime, sequence_number: int
) -> EventoModel:
    return EventoModel(
        aggregate_type="Evaluacion",
        aggregate_id=aggregate_id,
        sequence_number=sequence_number,
        event_type=event_type,
        payload=payload,
        occurred_at=occurred_at,
    )


class TestResumenDeStream:
    def test_evaluacion_recien_iniciada_es_en_curso(self):
        evaluacion_id, actividad_id = uuid4(), uuid4()
        iniciada_en = datetime(2026, 1, 1, tzinfo=UTC)
        eventos = [
            _evento(
                evaluacion_id,
                "EvaluacionIniciada",
                {"actividad_id": str(actividad_id)},
                iniciada_en,
                1,
            )
        ]

        resumen = _resumen_de_stream(eventos)

        assert resumen.evaluacion_id == evaluacion_id
        assert resumen.actividad_id == actividad_id
        assert resumen.estado is EstadoEvaluacion.EN_CURSO
        assert resumen.ultima_actividad_en == iniciada_en

    def test_ultima_actividad_en_se_actualiza_con_respuesta_registrada(self):
        evaluacion_id, actividad_id = uuid4(), uuid4()
        iniciada_en = datetime(2026, 1, 1, tzinfo=UTC)
        respondida_en = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
        eventos = [
            _evento(
                evaluacion_id,
                "EvaluacionIniciada",
                {"actividad_id": str(actividad_id)},
                iniciada_en,
                1,
            ),
            _evento(evaluacion_id, "RespuestaRegistrada", {}, respondida_en, 2),
        ]

        resumen = _resumen_de_stream(eventos)

        assert resumen.estado is EstadoEvaluacion.EN_CURSO
        assert resumen.ultima_actividad_en == respondida_en

    def test_suspendida_no_cuenta_como_actividad(self):
        evaluacion_id, actividad_id = uuid4(), uuid4()
        iniciada_en = datetime(2026, 1, 1, tzinfo=UTC)
        suspendida_en = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
        eventos = [
            _evento(
                evaluacion_id,
                "EvaluacionIniciada",
                {"actividad_id": str(actividad_id)},
                iniciada_en,
                1,
            ),
            _evento(
                evaluacion_id, "EvaluacionSuspendida", {"actor": "estudiante"}, suspendida_en, 2
            ),
        ]

        resumen = _resumen_de_stream(eventos)

        assert resumen.estado is EstadoEvaluacion.SUSPENDIDA
        assert resumen.ultima_actividad_en == iniciada_en

    def test_reanudada_vuelve_a_en_curso_y_cuenta_como_actividad(self):
        evaluacion_id, actividad_id = uuid4(), uuid4()
        iniciada_en = datetime(2026, 1, 1, tzinfo=UTC)
        suspendida_en = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
        reanudada_en = datetime(2026, 1, 2, tzinfo=UTC)
        eventos = [
            _evento(
                evaluacion_id,
                "EvaluacionIniciada",
                {"actividad_id": str(actividad_id)},
                iniciada_en,
                1,
            ),
            _evento(
                evaluacion_id, "EvaluacionSuspendida", {"actor": "estudiante"}, suspendida_en, 2
            ),
            _evento(evaluacion_id, "EvaluacionReanudada", {}, reanudada_en, 3),
        ]

        resumen = _resumen_de_stream(eventos)

        assert resumen.estado is EstadoEvaluacion.EN_CURSO
        assert resumen.ultima_actividad_en == reanudada_en

    def test_finalizada(self):
        evaluacion_id, actividad_id = uuid4(), uuid4()
        iniciada_en = datetime(2026, 1, 1, tzinfo=UTC)
        finalizada_en = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
        eventos = [
            _evento(
                evaluacion_id,
                "EvaluacionIniciada",
                {"actividad_id": str(actividad_id)},
                iniciada_en,
                1,
            ),
            _evento(
                evaluacion_id, "EvaluacionFinalizada", {"actor": "estudiante"}, finalizada_en, 2
            ),
        ]

        resumen = _resumen_de_stream(eventos)

        assert resumen.estado is EstadoEvaluacion.FINALIZADA
