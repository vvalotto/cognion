import uuid

from src.identidad.entities.comision import Comision
from src.identidad.entities.eventos import InvitacionGenerada
from src.identidad.interface_adapters.controllers.invitaciones_controller import (
    InvitacionesController,
)
from src.identidad.use_cases.generar_invitacion import GenerarInvitacionUseCase
from tests.unit.inc1._fakes import (
    FakeComisionRepository,
    FakeInvitacionRepository,
    FakeNotificador,
)


class TestInvitacionesController:
    async def test_generar_invitacion_delega_al_use_case(self):
        comision_repo = FakeComisionRepository()
        invitacion_repo = FakeInvitacionRepository()
        notificador = FakeNotificador()
        docente_id = uuid.uuid4()
        comision = Comision.crear("IS", "lu 10-12", uuid.uuid4())
        comision.asignar_docente(docente_id)
        await comision_repo.guardar(comision)

        controller = InvitacionesController(
            GenerarInvitacionUseCase(comision_repo, invitacion_repo, notificador)
        )

        invitacion, evento = await controller.generar_invitacion(
            comision.id, docente_id, "estudiante@fiuner.edu.ar"
        )

        assert invitacion.docente_id == docente_id
        assert isinstance(evento, InvitacionGenerada)
