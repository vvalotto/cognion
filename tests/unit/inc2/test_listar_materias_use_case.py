from uuid import uuid4

from src.banco_preguntas.entities.banco import Banco
from src.banco_preguntas.entities.materia import Materia
from src.banco_preguntas.use_cases.listar_materias import ListarMateriasUseCase
from tests.unit.inc2._fakes import (
    FakeBancoRepository,
    FakeComisionConsultaPort,
    FakeMateriaRepository,
    FakePreguntaRepository,
)
from tests.unit.inc2.test_filtrar_banco_use_case import _pregunta_om, _pregunta_vf


class TestListarMateriasUseCase:
    async def test_sin_materias_devuelve_lista_vacia(self):
        use_case = ListarMateriasUseCase(
            FakeMateriaRepository(),
            FakeBancoRepository(),
            FakePreguntaRepository(),
            FakeComisionConsultaPort(),
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

        use_case = ListarMateriasUseCase(
            materia_repo, banco_repo, FakePreguntaRepository(), FakeComisionConsultaPort()
        )
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

        use_case = ListarMateriasUseCase(
            materia_repo, banco_repo, pregunta_repo, FakeComisionConsultaPort()
        )
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

        use_case = ListarMateriasUseCase(
            materia_repo, banco_repo, pregunta_repo, FakeComisionConsultaPort()
        )
        resultado = await use_case.execute()

        assert resultado == [(materia_1, banco_1, 1), (materia_2, banco_2, 3)]

    async def test_docente_ve_solo_sus_materias(self):
        """`US-ADJ-57`: con `docente_id`, el listado se acota a materias con Comisión asignada."""
        materia_repo = FakeMateriaRepository()
        banco_repo = FakeBancoRepository()
        pregunta_repo = FakePreguntaRepository()
        comision_consulta = FakeComisionConsultaPort()
        docente_id = uuid4()

        propia = Materia.crear("Ingeniería de Software")
        banco_propia = Banco.crear(propia.id)
        ajena = Materia.crear("Gestión de Proyectos")
        banco_ajena = Banco.crear(ajena.id)
        for materia in (propia, ajena):
            await materia_repo.guardar(materia)
        for banco in (banco_propia, banco_ajena):
            await banco_repo.guardar(banco)
        comision_consulta.docentes_asignados_por_materia[propia.id] = {docente_id}

        use_case = ListarMateriasUseCase(materia_repo, banco_repo, pregunta_repo, comision_consulta)
        resultado = await use_case.execute(docente_id=docente_id)

        assert resultado == [(propia, banco_propia, 0)]

    async def test_administrador_ve_todas_sin_filtrar(self):
        """`docente_id=None` (Administrador) — sin cambios respecto del comportamiento previo."""
        materia_repo = FakeMateriaRepository()
        banco_repo = FakeBancoRepository()
        pregunta_repo = FakePreguntaRepository()
        materia = Materia.crear("Ingeniería de Software")
        banco = Banco.crear(materia.id)
        await materia_repo.guardar(materia)
        await banco_repo.guardar(banco)

        use_case = ListarMateriasUseCase(
            materia_repo, banco_repo, pregunta_repo, FakeComisionConsultaPort()
        )
        resultado = await use_case.execute(docente_id=None)

        assert resultado == [(materia, banco, 0)]
