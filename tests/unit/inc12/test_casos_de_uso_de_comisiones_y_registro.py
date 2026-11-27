"""Casos de uso de consulta de comisiones y de registro con materia (`US-12.2.4`, ex lógica de controllers)."""

from uuid import UUID, uuid4

import pytest

from src.identidad.entities.comision import Comision
from src.identidad.entities.errors import (
    ComisionNoAutorizada,
    ComisionNoExiste,
    InvitacionInvalida,
    MateriaNoAutorizada,
    MateriaNoExiste,
)
from src.identidad.entities.invitacion import Invitacion
from src.identidad.entities.ports.comision_query_port import (
    ComisionQueryPort,
    EstudianteConEmail,
    EstudianteResumen,
)
from src.identidad.use_cases.listar_comisiones_de_materia import ListarComisionesDeMateriaUseCase
from src.identidad.use_cases.listar_estudiantes_de_comision import (
    ListarEstudiantesDeComisionUseCase,
)
from src.identidad.use_cases.obtener_comision import ObtenerComisionUseCase
from src.identidad.use_cases.registrar_estudiante import RegistrarEstudianteUseCase
from src.identidad.use_cases.registrar_estudiante_con_materia import (
    RegistrarEstudianteConMateriaUseCase,
)
from tests.unit.inc1._fakes import (
    FakeComisionRepository,
    FakeInvitacionRepository,
    FakeMateriaPort,
    FakePasswordHasher,
    FakeUsuarioRepository,
)


class _ComisionQueryPortFake(ComisionQueryPort):
    def __init__(self) -> None:
        self.comisiones_por_materia: dict[UUID, list[Comision]] = {}
        self.estudiantes_por_comision: dict[UUID, list[EstudianteResumen]] = {}

    async def listar_comisiones_por_materia(
        self, materia_id: UUID, incluir_inactivas: bool = False
    ) -> list[Comision]:
        return self.comisiones_por_materia.get(materia_id, [])

    async def listar_estudiantes(self, comision_id: UUID) -> list[EstudianteResumen]:
        return self.estudiantes_por_comision.get(comision_id, [])

    async def listar_estudiantes_con_email(self, comision_id: UUID) -> list[EstudianteConEmail]:
        return []

    async def tiene_comisiones_asignadas(self, docente_id: UUID) -> bool:
        return False

    async def docente_pertenece_a_comision(self, docente_id: UUID, comision_id: UUID) -> bool:
        for comisiones in self.comisiones_por_materia.values():
            for comision in comisiones:
                if comision.id == comision_id:
                    return docente_id in comision.docentes_asignados
        return False

    async def docente_tiene_comision_en_materia(self, docente_id: UUID, materia_id: UUID) -> bool:
        return any(
            docente_id in comision.docentes_asignados
            for comision in self.comisiones_por_materia.get(materia_id, [])
        )

    async def existe_comision_en_materia(self, materia_id: UUID) -> bool:
        return bool(self.comisiones_por_materia.get(materia_id))


class TestListarComisionesDeMateria:
    async def test_materia_con_comisiones(self):
        materia_id = uuid4()
        comision_query = _ComisionQueryPortFake()
        comision = Comision.crear(materia_id, "lu 10-12", uuid4())
        comision_query.comisiones_por_materia[materia_id] = [comision]
        materia_port = FakeMateriaPort()
        materia_port.agregar(materia_id, "Ingeniería de Software")

        resultado = await ListarComisionesDeMateriaUseCase(comision_query, materia_port).execute(
            materia_id
        )

        assert resultado == [comision]

    async def test_materia_inexistente_levanta_error(self):
        caso = ListarComisionesDeMateriaUseCase(_ComisionQueryPortFake(), FakeMateriaPort())

        with pytest.raises(MateriaNoExiste):
            await caso.execute(uuid4())

    async def test_docente_ve_solo_sus_comisiones(self):
        """`US-ADJ-57`: con `docente_id`, el resultado se acota a las comisiones propias."""
        materia_id = uuid4()
        docente_id = uuid4()
        propia = Comision.crear(materia_id, "lu 10-12", uuid4())
        propia.asignar_docente(docente_id)
        ajena = Comision.crear(materia_id, "ma 14-16", uuid4())
        ajena.asignar_docente(uuid4())
        comision_query = _ComisionQueryPortFake()
        comision_query.comisiones_por_materia[materia_id] = [propia, ajena]
        materia_port = FakeMateriaPort()
        materia_port.agregar(materia_id, "Ingeniería de Software")

        resultado = await ListarComisionesDeMateriaUseCase(comision_query, materia_port).execute(
            materia_id, docente_id=docente_id
        )

        assert resultado == [propia]

    async def test_docente_sin_ninguna_comision_en_la_materia_403(self):
        materia_id = uuid4()
        ajena = Comision.crear(materia_id, "ma 14-16", uuid4())
        ajena.asignar_docente(uuid4())
        comision_query = _ComisionQueryPortFake()
        comision_query.comisiones_por_materia[materia_id] = [ajena]
        materia_port = FakeMateriaPort()
        materia_port.agregar(materia_id, "Ingeniería de Software")
        caso = ListarComisionesDeMateriaUseCase(comision_query, materia_port)

        with pytest.raises(MateriaNoAutorizada):
            await caso.execute(materia_id, docente_id=uuid4())

    async def test_administrador_ve_todas_sin_filtrar(self):
        """`docente_id=None` (Administrador) — sin filtrar."""
        materia_id = uuid4()
        comision_a = Comision.crear(materia_id, "lu 10-12", uuid4())
        comision_a.asignar_docente(uuid4())
        comision_b = Comision.crear(materia_id, "ma 14-16", uuid4())
        comision_query = _ComisionQueryPortFake()
        comision_query.comisiones_por_materia[materia_id] = [comision_a, comision_b]
        materia_port = FakeMateriaPort()
        materia_port.agregar(materia_id, "Ingeniería de Software")

        resultado = await ListarComisionesDeMateriaUseCase(comision_query, materia_port).execute(
            materia_id, docente_id=None
        )

        assert resultado == [comision_a, comision_b]


class TestListarEstudiantesDeComision:
    async def test_comision_con_estudiantes(self):
        comision_repo = FakeComisionRepository()
        comision = Comision.crear(uuid4(), "lu 10-12", uuid4())
        await comision_repo.guardar(comision)
        comision_query = _ComisionQueryPortFake()
        estudiante = EstudianteResumen(id=uuid4(), nombre="Ana Pérez")
        comision_query.estudiantes_por_comision[comision.id] = [estudiante]

        resultado = await ListarEstudiantesDeComisionUseCase(comision_repo, comision_query).execute(
            comision.id
        )

        assert resultado == [estudiante]

    async def test_comision_sin_estudiantes(self):
        comision_repo = FakeComisionRepository()
        comision = Comision.crear(uuid4(), "lu 10-12", uuid4())
        await comision_repo.guardar(comision)

        resultado = await ListarEstudiantesDeComisionUseCase(
            comision_repo, _ComisionQueryPortFake()
        ).execute(comision.id)

        assert resultado == []

    async def test_comision_inexistente_levanta_error(self):
        caso = ListarEstudiantesDeComisionUseCase(
            FakeComisionRepository(), _ComisionQueryPortFake()
        )

        with pytest.raises(ComisionNoExiste):
            await caso.execute(uuid4())

    async def test_docente_no_asignado_403(self):
        """`US-ADJ-57`: el Docente que llama debe estar asignado a esta comisión puntual."""
        comision_repo = FakeComisionRepository()
        comision = Comision.crear(uuid4(), "lu 10-12", uuid4())
        comision.asignar_docente(uuid4())
        await comision_repo.guardar(comision)
        caso = ListarEstudiantesDeComisionUseCase(comision_repo, _ComisionQueryPortFake())

        with pytest.raises(ComisionNoAutorizada):
            await caso.execute(comision.id, docente_id=uuid4())

    async def test_docente_asignado_ve_el_roster(self):
        comision_repo = FakeComisionRepository()
        docente_id = uuid4()
        comision = Comision.crear(uuid4(), "lu 10-12", uuid4())
        comision.asignar_docente(docente_id)
        await comision_repo.guardar(comision)

        resultado = await ListarEstudiantesDeComisionUseCase(
            comision_repo, _ComisionQueryPortFake()
        ).execute(comision.id, docente_id=docente_id)

        assert resultado == []


class TestObtenerComision:
    async def test_comision_existente(self):
        comision_repo = FakeComisionRepository()
        comision = Comision.crear(uuid4(), "lu 10-12", uuid4())
        await comision_repo.guardar(comision)

        assert await ObtenerComisionUseCase(comision_repo).execute(comision.id) == comision

    async def test_comision_inexistente_levanta_error(self):
        with pytest.raises(ComisionNoExiste):
            await ObtenerComisionUseCase(FakeComisionRepository()).execute(uuid4())

    async def test_docente_no_asignado_403(self):
        comision_repo = FakeComisionRepository()
        comision = Comision.crear(uuid4(), "lu 10-12", uuid4())
        comision.asignar_docente(uuid4())
        await comision_repo.guardar(comision)

        with pytest.raises(ComisionNoAutorizada):
            await ObtenerComisionUseCase(comision_repo).execute(comision.id, docente_id=uuid4())

    async def test_docente_asignado_la_obtiene(self):
        comision_repo = FakeComisionRepository()
        docente_id = uuid4()
        comision = Comision.crear(uuid4(), "lu 10-12", uuid4())
        comision.asignar_docente(docente_id)
        await comision_repo.guardar(comision)

        resultado = await ObtenerComisionUseCase(comision_repo).execute(
            comision.id, docente_id=docente_id
        )

        assert resultado == comision


class TestRegistrarEstudianteConMateria:
    async def _armar(self):
        invitacion_repo = FakeInvitacionRepository()
        comision_repo = FakeComisionRepository()
        materia_port = FakeMateriaPort()
        materia_id = uuid4()
        materia_port.agregar(materia_id, "Ingeniería de Software")
        comision = Comision.crear(materia_id, "Lu-Mi 18-20", uuid4())
        await comision_repo.guardar(comision)
        invitacion = Invitacion.crear(comision.id, uuid4())
        await invitacion_repo.guardar(invitacion)
        registrar = RegistrarEstudianteUseCase(
            invitacion_repo, FakeUsuarioRepository(), FakePasswordHasher()
        )
        caso = RegistrarEstudianteConMateriaUseCase(registrar, comision_repo, materia_port)
        return caso, invitacion, comision

    async def test_devuelve_usuario_comision_y_nombre_de_materia(self):
        caso, invitacion, comision = await self._armar()

        resultado = await caso.execute(
            invitacion.token, "Nico", "nico@fiuner.edu.ar", "Password#123x"
        )

        assert resultado.usuario.email == "nico@fiuner.edu.ar"
        assert resultado.comision_id == comision.id
        assert resultado.materia_nombre == "Ingeniería de Software"

    async def test_un_error_del_registro_se_propaga(self):
        caso, _invitacion, _comision = await self._armar()

        with pytest.raises(InvitacionInvalida):
            await caso.execute("token-que-no-existe", "Nico", "nico@fiuner.edu.ar", "Password#123x")
