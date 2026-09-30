"""Tests unitarios del puerto y DTO de `SesionEnVivoDesempenoConsultaPort` (US-ADJ-56)."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.analytics.entities.ports.sesion_en_vivo_desempeno_consulta_port import (
    SesionEnVivoDesempenoConsultaPort,
    SesionEnVivoDesempenoResumen,
)


class TestSesionEnVivoDesempenoResumen:
    def test_es_inmutable(self):
        resumen = SesionEnVivoDesempenoResumen(
            sesion_id=uuid4(),
            comision_id=uuid4(),
            materia_id=uuid4(),
            finalizada_en=datetime(2026, 1, 1, tzinfo=UTC),
            cantidad_preguntas=5,
            cantidad_correctas=3,
            cantidad_incorrectas=2,
            puntaje_final=850,
            posicion=2,
            total_participantes=14,
        )

        with pytest.raises(AttributeError):
            resumen.puntaje_final = 0  # type: ignore[misc]

    def test_conserva_los_valores_recibidos(self):
        sesion_id, comision_id, materia_id = uuid4(), uuid4(), uuid4()
        resumen = SesionEnVivoDesempenoResumen(
            sesion_id=sesion_id,
            comision_id=comision_id,
            materia_id=materia_id,
            finalizada_en=datetime(2026, 1, 1, tzinfo=UTC),
            cantidad_preguntas=10,
            cantidad_correctas=7,
            cantidad_incorrectas=3,
            puntaje_final=1200,
            posicion=1,
            total_participantes=20,
        )

        assert resumen.sesion_id == sesion_id
        assert resumen.comision_id == comision_id
        assert resumen.materia_id == materia_id
        assert resumen.posicion == 1
        assert resumen.total_participantes == 20


class TestSesionEnVivoDesempenoConsultaPort:
    def test_es_abstracto_no_instanciable(self):
        with pytest.raises(TypeError):
            SesionEnVivoDesempenoConsultaPort()  # type: ignore[abstract]
