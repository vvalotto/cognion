import uuid

from src.banco_preguntas.entities.banco import Banco


class TestBancoCrear:
    def test_crea_asociado_a_materia(self):
        materia_id = uuid.uuid4()
        banco = Banco.crear(materia_id)

        assert banco.materia_id == materia_id
        assert banco.id is not None
