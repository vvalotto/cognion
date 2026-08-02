from src.banco_preguntas.entities.materia import Materia


class TestMateriaCrear:
    def test_crea_con_nombre(self):
        materia = Materia.crear("Ingeniería de Software")

        assert materia.nombre == "Ingeniería de Software"
        assert materia.id is not None
