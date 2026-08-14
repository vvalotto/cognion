from src.banco_preguntas.entities.banco import Banco
from src.banco_preguntas.entities.materia import Materia
from src.banco_preguntas.use_cases.listar_materias import ListarMateriasUseCase
from tests.unit.inc2._fakes import (
    FakeBancoRepository,
    FakeMateriaRepository,
    FakePreguntaRepository,
)
from tests.unit.inc2.test_filtrar_banco_use_case import _pregunta_om, _pregunta_vf


class TestListarMateriasUseCase:
    async def test_sin_materias_devuelve_lista_vacia(self):
        use_case = ListarMateriasUseCase(
            FakeMateriaRepository(), FakeBancoRepository(), FakePreguntaRepository()
        )

        resultado = await use_case.execute()

        assert resultado == []

    async def test_materia_sin_preguntas_devuelve_conteo_cero(self):
        materia_repo = FakeMateriaRepository()
        banco_repo = FakeBancoRepository()
        materia = Materia.crear("Ingeniería de Software")
        banco = Banco.crear(materia.id)
        await materia_repo.guardar(materia)
        await banco_repo.guardar(banco)

        use_case = ListarMateriasUseCase(materia_repo, banco_repo, FakePreguntaRepository())
        resultado = await use_case.execute()

        assert resultado == [(materia, banco, 0)]

    async def test_cuenta_solo_preguntas_activas(self):
        materia_repo = FakeMateriaRepository()
        banco_repo = FakeBancoRepository()
        pregunta_repo = FakePreguntaRepository()
        materia = Materia.crear("Gestión de Proyectos")
        banco = Banco.crear(materia.id)
        await materia_repo.guardar(materia)
        await banco_repo.guardar(banco)

        activas = [_pregunta_om(banco.id), _pregunta_vf(banco.id)]
        for pregunta in activas:
            await pregunta_repo.guardar(pregunta)
        inactiva = _pregunta_om(banco.id)
        inactiva.activa = False
        await pregunta_repo.guardar(inactiva)

        use_case = ListarMateriasUseCase(materia_repo, banco_repo, pregunta_repo)
        resultado = await use_case.execute()

        assert resultado == [(materia, banco, 2)]

    async def test_lista_varias_materias_cada_una_con_su_conteo(self):
        materia_repo = FakeMateriaRepository()
        banco_repo = FakeBancoRepository()
        pregunta_repo = FakePreguntaRepository()

        materia_1 = Materia.crear("Ingeniería de Software")
        banco_1 = Banco.crear(materia_1.id)
        materia_2 = Materia.crear("Gestión de Proyectos")
        banco_2 = Banco.crear(materia_2.id)
        for materia in (materia_1, materia_2):
            await materia_repo.guardar(materia)
        for banco in (banco_1, banco_2):
            await banco_repo.guardar(banco)

        await pregunta_repo.guardar(_pregunta_om(banco_1.id))
        for _ in range(3):
            await pregunta_repo.guardar(_pregunta_vf(banco_2.id))

        use_case = ListarMateriasUseCase(materia_repo, banco_repo, pregunta_repo)
        resultado = await use_case.execute()

        assert resultado == [(materia_1, banco_1, 1), (materia_2, banco_2, 3)]
