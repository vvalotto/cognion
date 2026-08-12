import uuid

from src.banco_preguntas.entities.materia import Materia
from src.banco_preguntas.use_cases.obtener_materia import ObtenerMateriaUseCase
from tests.unit.inc2._fakes import FakeMateriaRepository


class TestObtenerMateriaUseCase:
    async def test_devuelve_la_materia_existente(self):
        materia_repo = FakeMateriaRepository()
        materia = Materia.crear("Ingeniería de Software")
        await materia_repo.guardar(materia)

        use_case = ObtenerMateriaUseCase(materia_repo)
        resultado = await use_case.execute(materia.id)

        assert resultado is materia

    async def test_devuelve_none_si_no_existe(self):
        materia_repo = FakeMateriaRepository()
        use_case = ObtenerMateriaUseCase(materia_repo)

        resultado = await use_case.execute(uuid.uuid4())

        assert resultado is None
