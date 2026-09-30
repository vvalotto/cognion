import uuid

from src.identidad.entities.comision import Comision
from src.identidad.entities.eventos import InvitacionGenerada
from src.identidad.entities.invitacion import Invitacion
from src.identidad.interface_adapters.controllers.invitaciones_controller import (
    InvitacionesController,
)
from src.identidad.use_cases.generar_invitacion import GenerarInvitacionUseCase
from src.identidad.use_cases.obtener_invitacion import InvitacionPreview, ObtenerInvitacionUseCase
from tests.unit.inc1._fakes import (
    FakeComisionRepository,
    FakeInvitacionRepository,
    FakeMateriaPort,
    FakeNotificador,
)


class TestInvitacionesController:
    async def test_generar_invitacion_delega_al_use_case(self):
        comision_repo = FakeComisionRepository()
        invitacion_repo = FakeInvitacionRepository()
        notificador = FakeNotificador()
        docente_id = uuid.uuid4()
        comision = Comision.crear(uuid.uuid4(), "lu 10-12", uuid.uuid4())
        comision.asignar_docente(docente_id)
        await comision_repo.guardar(comision)

        controller = InvitacionesController(
            GenerarInvitacionUseCase(comision_repo, invitacion_repo, notificador),
            ObtenerInvitacionUseCase(invitacion_repo, comision_repo, FakeMateriaPort()),
        )

        invitacion, evento = await controller.generar_invitacion(
            comision.id, docente_id, "estudiante@fiuner.edu.ar", solicitante_id=docente_id
        )

        assert invitacion.docente_id == docente_id
        assert isinstance(evento, InvitacionGenerada)

    async def test_generar_invitacion_sin_email_destinatario(self):
        """`US-ADJ-26`: el controller propaga `email_destinatario=None` sin error."""
        comision_repo = FakeComisionRepository()
        invitacion_repo = FakeInvitacionRepository()
        notificador = FakeNotificador()
        docente_id = uuid.uuid4()
        comision = Comision.crear(uuid.uuid4(), "lu 10-12", uuid.uuid4())
        comision.asignar_docente(docente_id)
        await comision_repo.guardar(comision)

        controller = InvitacionesController(
            GenerarInvitacionUseCase(comision_repo, invitacion_repo, notificador),
            ObtenerInvitacionUseCase(invitacion_repo, comision_repo, FakeMateriaPort()),
        )

        invitacion, evento = await controller.generar_invitacion(
            comision.id, docente_id, None, solicitante_id=docente_id
        )

        assert invitacion.docente_id == docente_id
        assert isinstance(evento, InvitacionGenerada)
        assert notificador.enviados == []

    async def test_obtener_invitacion_delega_al_use_case(self):
        comision_repo = FakeComisionRepository()
        invitacion_repo = FakeInvitacionRepository()
        notificador = FakeNotificador()
        materia_port = FakeMateriaPort()
        materia_id = uuid.uuid4()
        materia_port.agregar(materia_id, "Ingeniería de Software")
        comision = Comision.crear(materia_id, "lu 10-12", uuid.uuid4())
        await comision_repo.guardar(comision)
        invitacion = Invitacion.crear(comision.id, uuid.uuid4())
        await invitacion_repo.guardar(invitacion)

        controller = InvitacionesController(
            GenerarInvitacionUseCase(comision_repo, invitacion_repo, notificador),
            ObtenerInvitacionUseCase(invitacion_repo, comision_repo, materia_port),
        )

        preview = await controller.obtener_invitacion(invitacion.token)

        assert preview == InvitacionPreview(materia="Ingeniería de Software", horario="lu 10-12")
