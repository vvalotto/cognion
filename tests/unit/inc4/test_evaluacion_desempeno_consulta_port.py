"""Tests unitarios del puerto y DTO de `EvaluacionDesempenoConsultaPort` (US-4.1.1, US-4.2.4)."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.analytics.entities.ports.evaluacion_desempeno_consulta_port import (
    EvaluacionDesempenoConsultaPort,
    EvaluacionDesempenoResumen,
    RespuestaVigente,
)


class TestEvaluacionDesempenoResumen:
    def test_es_inmutable(self):
        resumen = EvaluacionDesempenoResumen(
            evaluacion_id=uuid4(),
            actividad_id=uuid4(),
            materia_id=uuid4(),
            finalizada_en=datetime(2026, 1, 1, tzinfo=UTC),
            cantidad_correctas=8,
            cantidad_incorrectas=2,
        )

        with pytest.raises(AttributeError):
            resumen.cantidad_correctas = 9  # type: ignore[misc]

    def test_conserva_los_conteos_recibidos(self):
        resumen = EvaluacionDesempenoResumen(
            evaluacion_id=uuid4(),
            actividad_id=uuid4(),
            materia_id=uuid4(),
            finalizada_en=datetime(2026, 1, 1, tzinfo=UTC),
            cantidad_correctas=5,
            cantidad_incorrectas=3,
        )

        assert resumen.cantidad_correctas == 5
        assert resumen.cantidad_incorrectas == 3


class TestRespuestaVigente:
    def test_es_inmutable(self):
        respuesta = RespuestaVigente(pregunta_id=uuid4(), estudiante_id=uuid4(), es_correcta=True)

        with pytest.raises(AttributeError):
            respuesta.es_correcta = False  # type: ignore[misc]

    def test_conserva_los_valores_recibidos(self):
        pregunta_id, estudiante_id = uuid4(), uuid4()
        respuesta = RespuestaVigente(
            pregunta_id=pregunta_id, estudiante_id=estudiante_id, es_correcta=False
        )

        assert respuesta.pregunta_id == pregunta_id
        assert respuesta.estudiante_id == estudiante_id
        assert respuesta.es_correcta is False


class TestEvaluacionDesempenoConsultaPort:
    def test_es_abstracto_no_instanciable(self):
        with pytest.raises(TypeError):
            EvaluacionDesempenoConsultaPort()  # type: ignore[abstract]
