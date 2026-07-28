import uuid

from src.identidad.entities.comision import Comision
from src.identidad.entities.eventos import InvitacionAceptada, UsuarioRegistrado
from src.identidad.entities.invitacion import Invitacion
from src.identidad.interface_adapters.controllers.registro_controller import RegistroController
from src.identidad.use_cases.registrar_estudiante import RegistrarEstudianteUseCase
from tests.unit.inc1._fakes import (
    FakeComisionRepository,
    FakeInvitacionRepository,
    FakePasswordHasher,
    FakeUsuarioRepository,
)


class TestRegistroController:
    async def test_registrar_estudiante_delega_al_use_case(self):
        invitacion_repo = FakeInvitacionRepository()
        usuario_repo = FakeUsuarioRepository()
        comision_repo = FakeComisionRepository()
        hasher = FakePasswordHasher()
        comision_id = uuid.uuid4()
        comision = Comision.crear("Ingeniería de Software", "Lu-Mi 18-20", uuid.uuid4())
        comision.id = comision_id
        await comision_repo.guardar(comision)
        invitacion = Invitacion.crear(comision_id, uuid.uuid4())
        await invitacion_repo.guardar(invitacion)

        controller = RegistroController(
            RegistrarEstudianteUseCase(invitacion_repo, usuario_repo, comision_repo, hasher)
        )

        usuario, materia, evento_invitacion, evento_usuario = await controller.registrar_estudiante(
            invitacion.token, "Nico", "nico@fiuner.edu.ar", "password123"
        )

        assert usuario.email == "nico@fiuner.edu.ar"
        assert materia == "Ingeniería de Software"
        assert isinstance(evento_invitacion, InvitacionAceptada)
        assert isinstance(evento_usuario, UsuarioRegistrado)
