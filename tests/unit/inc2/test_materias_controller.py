from src.banco_preguntas.entities.banco import Banco
from src.banco_preguntas.entities.eventos import BancoCreado, MateriaCreada
from src.banco_preguntas.entities.materia import Materia
from src.banco_preguntas.interface_adapters.controllers.materias_controller import (
    MateriasController,
)
from src.banco_preguntas.use_cases.crear_materia import CrearMateriaUseCase
from src.banco_preguntas.use_cases.listar_materias import ListarMateriasUseCase
from tests.unit.inc2._fakes import (
    FakeBancoRepository,
    FakeMateriaRepository,
    FakePreguntaRepository,
)


def _controller(materia_repo=None, banco_repo=None, pregunta_repo=None):
    materia_repo = materia_repo or FakeMateriaRepository()
    banco_repo = banco_repo or FakeBancoRepository()
    pregunta_repo = pregunta_repo or FakePreguntaRepository()
    return MateriasController(
        CrearMateriaUseCase(materia_repo, banco_repo),
        ListarMateriasUseCase(materia_repo, banco_repo, pregunta_repo),
    )


class TestMateriasController:
    async def test_crear_materia_delega_al_use_case(self):
        controller = _controller()

        materia, banco, evento_materia, evento_banco = await controller.crear_materia(
            "Gestión de Proyectos"
        )

        assert materia.nombre == "Gestión de Proyectos"
        assert banco.materia_id == materia.id
        assert isinstance(evento_materia, MateriaCreada)
        assert isinstance(evento_banco, BancoCreado)

    async def test_listar_materias_delega_al_use_case(self):
        materia_repo = FakeMateriaRepository()
        banco_repo = FakeBancoRepository()
        materia = Materia.crear("Ingeniería de Software")
        banco = Banco.crear(materia.id)
        await materia_repo.guardar(materia)
        await banco_repo.guardar(banco)
        controller = _controller(materia_repo=materia_repo, banco_repo=banco_repo)

        resultado = await controller.listar_materias()

        assert resultado == [(materia, banco, 0)]
