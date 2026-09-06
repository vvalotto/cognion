"""Tests unitarios de los errores de dominio del BC Analytics (US-4.2.4)."""

from uuid import uuid4

from src.analytics.entities.errors import ComisionNoPerteneceAMateria


class TestComisionNoPerteneceAMateria:
    def test_mensaje_incluye_ambos_ids(self):
        comision_id, materia_id = uuid4(), uuid4()

        error = ComisionNoPerteneceAMateria(comision_id, materia_id)

        assert str(comision_id) in str(error)
        assert str(materia_id) in str(error)
