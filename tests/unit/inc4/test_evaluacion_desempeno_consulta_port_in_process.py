"""Tests unitarios de las funciones puras del adapter in-process (US-4.1.1).

Sin sesión de BD — mismo criterio que `tests/unit/inc3/test_evaluacion_activa_query_repository.py`:
`EventoModel` se instancia directamente en memoria, sin persistir.
"""

from datetime import UTC, datetime
from uuid import uuid4

from src.actividad_evaluativa.frameworks.db.models import EventoModel
from src.analytics.frameworks.adapters.evaluacion_desempeno_consulta_port_in_process import (
    EvaluacionDesempenoConsultaPortInProcess,
    _contar_respuestas_vigentes,
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


class TestContarRespuestasVigentes:
    def test_sin_respuestas_devuelve_ceros(self):
        eventos = [_evento(uuid4(), "EvaluacionIniciada", {}, 1)]

        correctas, incorrectas = _contar_respuestas_vigentes(eventos)

        assert (correctas, incorrectas) == (0, 0)

    def test_cuenta_correctas_e_incorrectas_sin_reintentos(self):
        pregunta_1, pregunta_2, pregunta_3 = uuid4(), uuid4(), uuid4()
        eventos = [
            _respuesta(pregunta_1, True, 1),
            _respuesta(pregunta_2, False, 2),
            _respuesta(pregunta_3, True, 3),
        ]

        correctas, incorrectas = _contar_respuestas_vigentes(eventos)

        assert (correctas, incorrectas) == (2, 1)

    def test_reintento_posterior_reemplaza_al_anterior(self):
        """Misma pregunta respondida dos veces: cuenta solo la más reciente (INV-AE-09)."""
        pregunta_id = uuid4()
        eventos = [
            _respuesta(pregunta_id, False, 1),
            _respuesta(pregunta_id, True, 2),
        ]

        correctas, incorrectas = _contar_respuestas_vigentes(eventos)

        assert (correctas, incorrectas) == (1, 0)

    def test_ignora_eventos_que_no_son_respuesta(self):
        eventos = [
            _evento(uuid4(), "EvaluacionIniciada", {}, 1),
            _respuesta(uuid4(), True, 2),
            _evento(uuid4(), "EvaluacionFinalizada", {"actor": "estudiante"}, 3),
        ]

        correctas, incorrectas = _contar_respuestas_vigentes(eventos)

        assert (correctas, incorrectas) == (1, 0)


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
        adapter = EvaluacionDesempenoConsultaPortInProcess(session=None)  # type: ignore[arg-type]

        resumen = adapter._resumen_de_stream(  # pylint: disable=protected-access
            eventos, {actividad_id: materia_id}
        )

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
        adapter = EvaluacionDesempenoConsultaPortInProcess(session=None)  # type: ignore[arg-type]

        resumen = adapter._resumen_de_stream(  # pylint: disable=protected-access
            eventos, {actividad_id: materia_id}
        )

        assert resumen is not None
        assert resumen.evaluacion_id == evaluacion_id
        assert resumen.actividad_id == actividad_id
        assert resumen.materia_id == materia_id
        assert resumen.finalizada_en == finalizada_en
        assert resumen.cantidad_correctas == 1
        assert resumen.cantidad_incorrectas == 1
