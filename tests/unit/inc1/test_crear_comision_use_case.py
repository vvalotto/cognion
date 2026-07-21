import uuid

from src.identidad.entities.eventos import ComisionCreada
from src.identidad.use_cases.crear_comision import CrearComisionUseCase
from tests.unit.inc1._fakes import FakeComisionRepository


class TestCrearComisionUseCase:
    async def test_crea_comision_con_docentes_vacio(self):
        repo = FakeComisionRepository()
        use_case = CrearComisionUseCase(repo)
        admin_id = uuid.uuid4()

        comision, evento = await use_case.execute("Ingeniería de Software", "lu 10-12", admin_id)

        assert comision.docentes_asignados == []
        assert isinstance(evento, ComisionCreada)
        assert evento.comision_id == comision.id
        assert repo.comisiones[comision.id] is comision
