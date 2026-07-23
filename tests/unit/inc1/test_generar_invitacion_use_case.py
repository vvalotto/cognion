import uuid

import pytest

from src.identidad.entities.comision import Comision
from src.identidad.entities.errors import ComisionNoExiste, DocenteNoAsignadoAComision
from src.identidad.entities.eventos import InvitacionGenerada
from src.identidad.use_cases.generar_invitacion import GenerarInvitacionUseCase
from tests.unit.inc1._fakes import (
    FakeComisionRepository,
    FakeInvitacionRepository,
    FakeNotificador,
)


class TestGenerarInvitacionUseCase:
    async def test_genera_invitacion_para_docente_asignado(self):
        comision_repo = FakeComisionRepository()
        invitacion_repo = FakeInvitacionRepository()
        notificador = FakeNotificador()
        docente_id = uuid.uuid4()
        comision = Comision.crear("IS", "lu 10-12", uuid.uuid4())
        comision.asignar_docente(docente_id)
        await comision_repo.guardar(comision)

        use_case = GenerarInvitacionUseCase(comision_repo, invitacion_repo, notificador)
        invitacion, evento = await use_case.execute(
            comision.id, docente_id, "estudiante@fiuner.edu.ar"
        )

        assert invitacion.comision_id == comision.id
        assert invitacion.docente_id == docente_id
        assert invitacion.id in invitacion_repo.invitaciones
        assert isinstance(evento, InvitacionGenerada)
        assert evento.token == invitacion.token

    async def test_envia_email_al_destinatario_indicado(self):
        comision_repo = FakeComisionRepository()
        invitacion_repo = FakeInvitacionRepository()
        notificador = FakeNotificador()
        docente_id = uuid.uuid4()
        comision = Comision.crear("IS", "lu 10-12", uuid.uuid4())
        comision.asignar_docente(docente_id)
        await comision_repo.guardar(comision)

        use_case = GenerarInvitacionUseCase(comision_repo, invitacion_repo, notificador)
        invitacion, _evento = await use_case.execute(
            comision.id, docente_id, "estudiante@fiuner.edu.ar"
        )

        assert notificador.enviados == [("estudiante@fiuner.edu.ar", invitacion.token)]

    async def test_rechaza_docente_no_asignado_a_la_comision(self):
        comision_repo = FakeComisionRepository()
        invitacion_repo = FakeInvitacionRepository()
        notificador = FakeNotificador()
        comision = Comision.crear("IS", "lu 10-12", uuid.uuid4())
        await comision_repo.guardar(comision)
        docente_no_asignado = uuid.uuid4()

        use_case = GenerarInvitacionUseCase(comision_repo, invitacion_repo, notificador)

        with pytest.raises(DocenteNoAsignadoAComision):
            await use_case.execute(comision.id, docente_no_asignado, "estudiante@fiuner.edu.ar")

        assert invitacion_repo.invitaciones == {}
        assert notificador.enviados == []

    async def test_rechaza_comision_inexistente(self):
        comision_repo = FakeComisionRepository()
        invitacion_repo = FakeInvitacionRepository()
        notificador = FakeNotificador()

        use_case = GenerarInvitacionUseCase(comision_repo, invitacion_repo, notificador)

        with pytest.raises(ComisionNoExiste):
            await use_case.execute(uuid.uuid4(), uuid.uuid4(), "estudiante@fiuner.edu.ar")

        assert invitacion_repo.invitaciones == {}
        assert notificador.enviados == []
