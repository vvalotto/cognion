import uuid

import pytest

from src.identidad.entities.comision import Comision
from src.identidad.entities.errors import ComisionNoExiste, MateriaNoExiste, UsuarioNoExiste
from src.identidad.entities.usuario import Usuario
from src.identidad.use_cases.listar_materias_del_estudiante import (
    ListarMateriasDelEstudianteUseCase,
)
from tests.unit.inc1._fakes import FakeComisionRepository, FakeMateriaPort, FakeUsuarioRepository


def _crear_estudiante_con_comision(
    usuario_repo: FakeUsuarioRepository,
    comision_repo: FakeComisionRepository,
    materia_port: FakeMateriaPort,
    materia_id: uuid.UUID,
    nombre_materia: str,
) -> Usuario:
    comision = Comision.crear(materia_id, "lu 10-12", uuid.uuid4())
    comision_repo.comisiones[comision.id] = comision
    materia_port.agregar(materia_id, nombre_materia)
    usuario = Usuario.crear_estudiante("Juana Pérez", "juana@example.com", "hash", comision.id)
    usuario_repo.usuarios[usuario.id] = usuario
    return usuario


class TestListarMateriasDelEstudianteUseCase:
    async def test_devuelve_la_materia_de_su_comision(self):
        usuario_repo = FakeUsuarioRepository()
        comision_repo = FakeComisionRepository()
        materia_port = FakeMateriaPort()
        materia_id = uuid.uuid4()
        estudiante = _crear_estudiante_con_comision(
            usuario_repo, comision_repo, materia_port, materia_id, "Ingeniería de Software"
        )
        use_case = ListarMateriasDelEstudianteUseCase(usuario_repo, comision_repo, materia_port)

        resultado = await use_case.execute(estudiante.id)

        assert len(resultado) == 1
        assert resultado[0].id == materia_id
        assert resultado[0].nombre == "Ingeniería de Software"

    async def test_rechaza_estudiante_inexistente(self):
        usuario_repo = FakeUsuarioRepository()
        comision_repo = FakeComisionRepository()
        materia_port = FakeMateriaPort()
        use_case = ListarMateriasDelEstudianteUseCase(usuario_repo, comision_repo, materia_port)

        with pytest.raises(UsuarioNoExiste):
            await use_case.execute(uuid.uuid4())

    async def test_rechaza_comision_inexistente(self):
        usuario_repo = FakeUsuarioRepository()
        comision_repo = FakeComisionRepository()
        materia_port = FakeMateriaPort()
        estudiante = Usuario.crear_estudiante(
            "Juana Pérez", "juana@example.com", "hash", uuid.uuid4()
        )
        usuario_repo.usuarios[estudiante.id] = estudiante
        use_case = ListarMateriasDelEstudianteUseCase(usuario_repo, comision_repo, materia_port)

        with pytest.raises(ComisionNoExiste):
            await use_case.execute(estudiante.id)

    async def test_rechaza_materia_inexistente(self):
        usuario_repo = FakeUsuarioRepository()
        comision_repo = FakeComisionRepository()
        materia_port = FakeMateriaPort()
        comision = Comision.crear(uuid.uuid4(), "lu 10-12", uuid.uuid4())
        comision_repo.comisiones[comision.id] = comision
        estudiante = Usuario.crear_estudiante(
            "Juana Pérez", "juana@example.com", "hash", comision.id
        )
        usuario_repo.usuarios[estudiante.id] = estudiante
        use_case = ListarMateriasDelEstudianteUseCase(usuario_repo, comision_repo, materia_port)

        with pytest.raises(MateriaNoExiste):
            await use_case.execute(estudiante.id)
