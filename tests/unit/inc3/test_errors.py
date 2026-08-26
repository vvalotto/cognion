from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.actividad_evaluativa.entities.errors import (
    CantidadIntentosInvalida,
    ConcurrenciaOptimistaError,
    MateriaNoExiste,
    PeriodoInvalido,
    PreguntasInsuficientes,
)


class TestConcurrenciaOptimistaError:
    def test_guarda_stream_y_numeros_en_conflicto(self):
        aggregate_id = uuid4()

        error = ConcurrenciaOptimistaError(
            aggregate_type="Evaluacion",
            aggregate_id=aggregate_id,
            expected_sequence_number=1,
            actual_sequence_number=2,
        )

        assert error.aggregate_type == "Evaluacion"
        assert error.aggregate_id == aggregate_id
        assert error.expected_sequence_number == 1
        assert error.actual_sequence_number == 2

    def test_mensaje_incluye_stream_y_numeros(self):
        aggregate_id = uuid4()

        error = ConcurrenciaOptimistaError(
            aggregate_type="Evaluacion",
            aggregate_id=aggregate_id,
            expected_sequence_number=1,
            actual_sequence_number=2,
        )

        mensaje = str(error)
        assert "Evaluacion" in mensaje
        assert str(aggregate_id) in mensaje
        assert "1" in mensaje
        assert "2" in mensaje


class TestMateriaNoExiste:
    def test_guarda_materia_id_y_arma_mensaje(self):
        materia_id = uuid4()

        error = MateriaNoExiste(materia_id)

        assert error.materia_id == materia_id
        assert str(materia_id) in str(error)


class TestPreguntasInsuficientes:
    def test_guarda_cantidades_y_arma_mensaje(self):
        error = PreguntasInsuficientes(cantidad_solicitada=10, cantidad_disponible=5)

        assert error.cantidad_solicitada == 10
        assert error.cantidad_disponible == 5
        assert "10" in str(error)
        assert "5" in str(error)


class TestPeriodoInvalido:
    def test_guarda_fechas_y_arma_mensaje(self):
        apertura = datetime.now(UTC)
        cierre = apertura - timedelta(days=1)

        error = PeriodoInvalido(apertura, cierre)

        assert error.fecha_apertura == apertura
        assert error.fecha_cierre == cierre


class TestCantidadIntentosInvalida:
    def test_guarda_cantidad_y_arma_mensaje(self):
        error = CantidadIntentosInvalida(0)

        assert error.cantidad_intentos_permitidos == 0
        assert "0" in str(error)
