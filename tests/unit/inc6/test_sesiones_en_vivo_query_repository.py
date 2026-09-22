"""Tests unitarios de `_resumen_de_stream` de `sesiones_en_vivo_query_repository` (US-6.3.2)."""

from datetime import UTC, datetime
from uuid import uuid4

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import EstadoSesionEnVivo
from src.actividad_evaluativa.frameworks.adapters.sesiones_en_vivo_query_repository import (
    _resumen_de_stream,
)
from src.actividad_evaluativa.frameworks.db.models import EventoModel


def _evento(
    aggregate_id, event_type: str, payload: dict, occurred_at: datetime, sequence_number: int
) -> EventoModel:
    return EventoModel(
        aggregate_type="ActividadEvaluativaEnVivo",
        aggregate_id=aggregate_id,
        sequence_number=sequence_number,
        event_type=event_type,
        payload=payload,
        occurred_at=occurred_at,
    )


def _payload_creada(comision_id, materia_id, **extra) -> dict:
    base = {
        "sesion_id": str(uuid4()),
        "comision_id": str(comision_id),
        "materia_id": str(materia_id),
        "preguntas": [{"pregunta_id": str(uuid4()), "orden": 0} for _ in range(5)],
        "tiempo_limite_por_pregunta_segundos": 30,
        "unidad_tematica": None,
        "tema": None,
    }
    base.update(extra)
    return base


class TestResumenDeStream:
    def test_recien_creada_es_en_espera(self):
        sesion_id, comision_id, materia_id = uuid4(), uuid4(), uuid4()
        creada_en = datetime(2026, 1, 1, tzinfo=UTC)
        eventos = [
            _evento(
                sesion_id,
                "SesionEnVivoCreada",
                _payload_creada(comision_id, materia_id),
                creada_en,
                1,
            )
        ]

        resumen = _resumen_de_stream(eventos)

        assert resumen.id == sesion_id
        assert resumen.comision_id == comision_id
        assert resumen.materia_id == materia_id
        assert resumen.cantidad_preguntas == 5
        assert resumen.tiempo_limite_por_pregunta_segundos == 30
        assert resumen.estado is EstadoSesionEnVivo.EN_ESPERA
        assert resumen.creada_en == creada_en

    def test_iniciada_pasa_a_en_curso(self):
        sesion_id, comision_id, materia_id = uuid4(), uuid4(), uuid4()
        eventos = [
            _evento(
                sesion_id,
                "SesionEnVivoCreada",
                _payload_creada(comision_id, materia_id),
                datetime(2026, 1, 1, tzinfo=UTC),
                1,
            ),
            _evento(sesion_id, "SesionEnVivoIniciada", {}, datetime(2026, 1, 1, 12, tzinfo=UTC), 2),
        ]

        resumen = _resumen_de_stream(eventos)

        assert resumen.estado is EstadoSesionEnVivo.EN_CURSO

    def test_eventos_intermedios_no_cambian_el_estado(self):
        sesion_id, comision_id, materia_id = uuid4(), uuid4(), uuid4()
        eventos = [
            _evento(
                sesion_id,
                "SesionEnVivoCreada",
                _payload_creada(comision_id, materia_id),
                datetime(2026, 1, 1, tzinfo=UTC),
                1,
            ),
            _evento(sesion_id, "SesionEnVivoIniciada", {}, datetime(2026, 1, 1, 12, tzinfo=UTC), 2),
            _evento(
                sesion_id, "OpcionesEnVivoMostradas", {}, datetime(2026, 1, 1, 13, tzinfo=UTC), 3
            ),
            _evento(
                sesion_id, "PreguntaEnVivoCerrada", {}, datetime(2026, 1, 1, 14, tzinfo=UTC), 4
            ),
        ]

        resumen = _resumen_de_stream(eventos)

        assert resumen.estado is EstadoSesionEnVivo.EN_CURSO

    def test_finalizada(self):
        sesion_id, comision_id, materia_id = uuid4(), uuid4(), uuid4()
        eventos = [
            _evento(
                sesion_id,
                "SesionEnVivoCreada",
                _payload_creada(comision_id, materia_id),
                datetime(2026, 1, 1, tzinfo=UTC),
                1,
            ),
            _evento(sesion_id, "SesionEnVivoIniciada", {}, datetime(2026, 1, 1, 12, tzinfo=UTC), 2),
            _evento(
                sesion_id, "SesionEnVivoFinalizada", {}, datetime(2026, 1, 1, 13, tzinfo=UTC), 3
            ),
        ]

        resumen = _resumen_de_stream(eventos)

        assert resumen.estado is EstadoSesionEnVivo.FINALIZADA

    def test_unidad_tematica_y_tema_se_propagan(self):
        sesion_id, comision_id, materia_id = uuid4(), uuid4(), uuid4()
        eventos = [
            _evento(
                sesion_id,
                "SesionEnVivoCreada",
                _payload_creada(
                    comision_id, materia_id, unidad_tematica="Unidad 1", tema="Bounded Contexts"
                ),
                datetime(2026, 1, 1, tzinfo=UTC),
                1,
            )
        ]

        resumen = _resumen_de_stream(eventos)

        assert resumen.unidad_tematica == "Unidad 1"
        assert resumen.tema == "Bounded Contexts"
