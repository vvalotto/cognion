from uuid import uuid4

from src.actividad_evaluativa.entities.errors import ConcurrenciaOptimistaError


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
