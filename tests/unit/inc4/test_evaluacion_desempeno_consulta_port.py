"""Tests unitarios del puerto y DTO de `EvaluacionDesempenoConsultaPort` (US-4.1.1)."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.analytics.entities.ports.evaluacion_desempeno_consulta_port import (
    EvaluacionDesempenoConsultaPort,
    EvaluacionDesempenoResumen,
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


class TestEvaluacionDesempenoConsultaPort:
    def test_es_abstracto_no_instanciable(self):
        with pytest.raises(TypeError):
            EvaluacionDesempenoConsultaPort()  # type: ignore[abstract]
