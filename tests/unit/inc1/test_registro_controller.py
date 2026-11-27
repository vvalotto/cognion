import uuid

from src.identidad.entities.comision import Comision
from src.identidad.entities.invitacion import Invitacion
from src.identidad.interface_adapters.controllers.registro_controller import RegistroController
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


class TestRegistroController:
    async def test_registrar_estudiante_delega_al_use_case(self):
        invitacion_repo = FakeInvitacionRepository()
        usuario_repo = FakeUsuarioRepository()
        comision_repo = FakeComisionRepository()
        hasher = FakePasswordHasher()
        materia_port = FakeMateriaPort()
        materia_id = uuid.uuid4()
        materia_port.agregar(materia_id, "Ingeniería de Software")
        comision_id = uuid.uuid4()
        comision = Comision.crear(materia_id, "Lu-Mi 18-20", uuid.uuid4())
        comision.id = comision_id
        await comision_repo.guardar(comision)
        invitacion = Invitacion.crear(comision_id, uuid.uuid4())
        await invitacion_repo.guardar(invitacion)

        controller = RegistroController(
            RegistrarEstudianteConMateriaUseCase(
                RegistrarEstudianteUseCase(invitacion_repo, usuario_repo, hasher),
                comision_repo,
                materia_port,
            )
        )

        salida = await controller.registrar_estudiante(
            invitacion.token, "Nico", "nico@fiuner.edu.ar", "Password#123x"
        )

        assert salida.email == "nico@fiuner.edu.ar"
        assert salida.materia == "Ingeniería de Software"
        assert salida.comision_id == comision_id
