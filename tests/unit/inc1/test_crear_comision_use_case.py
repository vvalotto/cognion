import uuid

import pytest

from src.identidad.entities.errors import MateriaNoExiste
from src.identidad.entities.eventos import ComisionCreada
from src.identidad.use_cases.crear_comision import CrearComisionUseCase
from tests.unit.inc1._fakes import FakeComisionRepository, FakeMateriaPort


class TestCrearComisionUseCase:
    async def test_crea_comision_con_docentes_vacio(self):
        repo = FakeComisionRepository()
        materia_port = FakeMateriaPort()
        materia_id = uuid.uuid4()
        materia_port.agregar(materia_id, "Ingeniería de Software")
        use_case = CrearComisionUseCase(repo, materia_port)
        admin_id = uuid.uuid4()

        comision, evento = await use_case.execute(materia_id, "lu 10-12", admin_id)

        assert comision.materia_id == materia_id
        assert comision.docentes_asignados == []
        assert isinstance(evento, ComisionCreada)
        assert evento.comision_id == comision.id
        assert evento.materia_id == materia_id
        assert repo.comisiones[comision.id] is comision

    async def test_rechaza_materia_inexistente(self):
        repo = FakeComisionRepository()
        materia_port = FakeMateriaPort()
        materia_id = uuid.uuid4()

        use_case = CrearComisionUseCase(repo, materia_port)

        with pytest.raises(MateriaNoExiste):
            await use_case.execute(materia_id, "lu 10-12", uuid.uuid4())

        assert repo.comisiones == {}
