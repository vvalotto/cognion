from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from src.actividad_evaluativa.entities.actividad_evaluativa_periodo_abierto import (
    ActividadEvaluativaPeriodoAbierto,
)
from src.actividad_evaluativa.entities.errors import CantidadIntentosInvalida, PeriodoInvalido


def _fechas() -> tuple[datetime, datetime]:
    apertura = datetime.now(UTC)
    cierre = apertura + timedelta(days=7)
    return apertura, cierre


class TestActividadEvaluativaPeriodoAbiertoCrear:
    def test_crea_actividad_valida(self):
        materia_id = uuid4()
        apertura, cierre = _fechas()

        actividad = ActividadEvaluativaPeriodoAbierto.crear(
            materia_id=materia_id,
            fecha_apertura=apertura,
            fecha_cierre=cierre,
            cantidad_preguntas=10,
            cantidad_intentos_permitidos=1,
        )

        assert actividad.materia_id == materia_id
        assert actividad.fecha_apertura == apertura
        assert actividad.fecha_cierre == cierre
        assert actividad.cantidad_preguntas == 10
        assert actividad.cantidad_intentos_permitidos == 1
        assert actividad.cerrada_manualmente is False
        assert actividad.id is not None

    def test_genera_id_distinto_por_actividad(self):
        apertura, cierre = _fechas()

        actividad_1 = ActividadEvaluativaPeriodoAbierto.crear(uuid4(), apertura, cierre, 10, 1)
        actividad_2 = ActividadEvaluativaPeriodoAbierto.crear(uuid4(), apertura, cierre, 10, 1)

        assert actividad_1.id != actividad_2.id

    def test_rechaza_apertura_igual_a_cierre(self):
        apertura, _ = _fechas()

        with pytest.raises(PeriodoInvalido):
            ActividadEvaluativaPeriodoAbierto.crear(uuid4(), apertura, apertura, 10, 1)

    def test_rechaza_apertura_posterior_a_cierre(self):
        apertura, cierre = _fechas()

        with pytest.raises(PeriodoInvalido):
            ActividadEvaluativaPeriodoAbierto.crear(uuid4(), cierre, apertura, 10, 1)

    def test_rechaza_cantidad_intentos_cero(self):
        apertura, cierre = _fechas()

        with pytest.raises(CantidadIntentosInvalida):
            ActividadEvaluativaPeriodoAbierto.crear(uuid4(), apertura, cierre, 10, 0)

    def test_rechaza_cantidad_intentos_negativa(self):
        apertura, cierre = _fechas()

        with pytest.raises(CantidadIntentosInvalida):
            ActividadEvaluativaPeriodoAbierto.crear(uuid4(), apertura, cierre, 10, -1)

    def test_acepta_cantidad_intentos_mayor_a_uno(self):
        apertura, cierre = _fechas()

        actividad = ActividadEvaluativaPeriodoAbierto.crear(uuid4(), apertura, cierre, 10, 3)

        assert actividad.cantidad_intentos_permitidos == 3
