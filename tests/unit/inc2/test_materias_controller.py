from src.banco_preguntas.entities.eventos import BancoCreado, MateriaCreada
from src.banco_preguntas.interface_adapters.controllers.materias_controller import (
    MateriasController,
)
from src.banco_preguntas.use_cases.crear_materia import CrearMateriaUseCase
from tests.unit.inc2._fakes import FakeBancoRepository, FakeMateriaRepository


class TestMateriasController:
    async def test_crear_materia_delega_al_use_case(self):
        materia_repo = FakeMateriaRepository()
        banco_repo = FakeBancoRepository()
        controller = MateriasController(CrearMateriaUseCase(materia_repo, banco_repo))

        materia, banco, evento_materia, evento_banco = await controller.crear_materia(
            "Gestión de Proyectos"
        )

        assert materia.nombre == "Gestión de Proyectos"
        assert banco.materia_id == materia.id
        assert isinstance(evento_materia, MateriaCreada)
        assert isinstance(evento_banco, BancoCreado)
