import uuid

from src.identidad.entities.eventos import ComisionCreada, DocenteAsignado
from src.identidad.entities.usuario import TipoPerfil, Usuario
from src.identidad.interface_adapters.controllers.comisiones_controller import (
    ComisionesController,
)
from src.identidad.use_cases.asignar_docente_a_comision import AsignarDocenteAComisionUseCase
from src.identidad.use_cases.crear_comision import CrearComisionUseCase
from tests.unit.inc1._fakes import FakeComisionRepository, FakeUsuarioRepository


class TestComisionesController:
    async def test_crear_comision_delega_al_use_case(self):
        comision_repo = FakeComisionRepository()
        usuario_repo = FakeUsuarioRepository()
        controller = ComisionesController(
            CrearComisionUseCase(comision_repo),
            AsignarDocenteAComisionUseCase(comision_repo, usuario_repo),
        )

        comision, evento = await controller.crear_comision(
            "Ingeniería de Software", "lu 10-12", uuid.uuid4()
        )

        assert comision.docentes_asignados == []
        assert isinstance(evento, ComisionCreada)

    async def test_asignar_docente_delega_al_use_case(self):
        comision_repo = FakeComisionRepository()
        usuario_repo = FakeUsuarioRepository()
        controller = ComisionesController(
            CrearComisionUseCase(comision_repo),
            AsignarDocenteAComisionUseCase(comision_repo, usuario_repo),
        )
        docente = Usuario.crear("Ana", "ana@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE)
        await usuario_repo.guardar(docente)
        comision, _ = await controller.crear_comision("IS", "lu 10-12", uuid.uuid4())

        resultado, evento = await controller.asignar_docente(comision.id, docente.id)

        assert docente.id in resultado.docentes_asignados
        assert isinstance(evento, DocenteAsignado)
