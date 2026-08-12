import pytest

from src.banco_preguntas.entities.errors import MateriaYaExiste
from src.banco_preguntas.entities.eventos import BancoCreado, MateriaCreada
from src.banco_preguntas.use_cases.crear_materia import CrearMateriaUseCase
from tests.unit.inc2._fakes import FakeBancoRepository, FakeMateriaRepository


class TestCrearMateriaUseCase:
    async def test_crea_materia_y_banco(self):
        materia_repo = FakeMateriaRepository()
        banco_repo = FakeBancoRepository()
        use_case = CrearMateriaUseCase(materia_repo, banco_repo)

        materia, banco, evento_materia, evento_banco = await use_case.execute(
            "Ingeniería de Software"
        )

        assert materia.nombre == "Ingeniería de Software"
        assert banco.materia_id == materia.id
        assert materia_repo.materias[materia.id] is materia
        assert banco_repo.bancos[banco.id] is banco
        assert isinstance(evento_materia, MateriaCreada)
        assert evento_materia.materia_id == materia.id
        assert isinstance(evento_banco, BancoCreado)
        assert evento_banco.banco_id == banco.id
        assert evento_banco.materia_id == materia.id

    async def test_rechaza_nombre_duplicado(self):
        materia_repo = FakeMateriaRepository()
        banco_repo = FakeBancoRepository()
        use_case = CrearMateriaUseCase(materia_repo, banco_repo)
        await use_case.execute("Ingeniería de Software")

        with pytest.raises(MateriaYaExiste):
            await use_case.execute("Ingeniería de Software")

        assert len(materia_repo.materias) == 1
        assert len(banco_repo.bancos) == 1
