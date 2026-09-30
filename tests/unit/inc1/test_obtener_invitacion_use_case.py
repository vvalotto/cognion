import uuid
from datetime import UTC, datetime, timedelta

import pytest

from src.identidad.entities.comision import Comision
from src.identidad.entities.errors import InvitacionInvalida, InvitacionVencida, InvitacionYaUsada
from src.identidad.entities.invitacion import Invitacion
from src.identidad.use_cases.obtener_invitacion import InvitacionPreview, ObtenerInvitacionUseCase
from tests.unit.inc1._fakes import (
    FakeComisionRepository,
    FakeInvitacionRepository,
    FakeMateriaPort,
)


class TestObtenerInvitacionUseCase:
    async def test_devuelve_materia_y_horario_de_invitacion_vigente(self):
        invitacion_repo = FakeInvitacionRepository()
        comision_repo = FakeComisionRepository()
        materia_port = FakeMateriaPort()
        materia_id = uuid.uuid4()
        materia_port.agregar(materia_id, "Ingeniería de Software")
        comision = Comision.crear(materia_id, "lu 10-12", uuid.uuid4())
        await comision_repo.guardar(comision)
        invitacion = Invitacion.crear(comision.id, uuid.uuid4())
        await invitacion_repo.guardar(invitacion)

        use_case = ObtenerInvitacionUseCase(invitacion_repo, comision_repo, materia_port)
        preview = await use_case.execute(invitacion.token)

        assert preview == InvitacionPreview(materia="Ingeniería de Software", horario="lu 10-12")

    async def test_no_consume_la_invitacion(self):
        invitacion_repo = FakeInvitacionRepository()
        comision_repo = FakeComisionRepository()
        materia_port = FakeMateriaPort()
        materia_id = uuid.uuid4()
        materia_port.agregar(materia_id, "Ingeniería de Software")
        comision = Comision.crear(materia_id, "lu 10-12", uuid.uuid4())
        await comision_repo.guardar(comision)
        invitacion = Invitacion.crear(comision.id, uuid.uuid4())
        await invitacion_repo.guardar(invitacion)

        use_case = ObtenerInvitacionUseCase(invitacion_repo, comision_repo, materia_port)
        await use_case.execute(invitacion.token)
        await use_case.execute(invitacion.token)

        invitacion_actual = await invitacion_repo.obtener_por_token(invitacion.token)
        assert invitacion_actual is not None
        assert invitacion_actual.usada_en is None

    async def test_token_inexistente_lanza_invitacion_invalida(self):
        invitacion_repo = FakeInvitacionRepository()
        comision_repo = FakeComisionRepository()
        materia_port = FakeMateriaPort()

        use_case = ObtenerInvitacionUseCase(invitacion_repo, comision_repo, materia_port)

        with pytest.raises(InvitacionInvalida):
            await use_case.execute("token-inexistente")

    async def test_invitacion_vencida_lanza_invitacion_vencida(self):
        invitacion_repo = FakeInvitacionRepository()
        comision_repo = FakeComisionRepository()
        materia_port = FakeMateriaPort()
        invitacion = Invitacion.crear(uuid.uuid4(), uuid.uuid4())
        invitacion.expira_en = datetime.now(UTC) - timedelta(days=1)
        await invitacion_repo.guardar(invitacion)

        use_case = ObtenerInvitacionUseCase(invitacion_repo, comision_repo, materia_port)

        with pytest.raises(InvitacionVencida):
            await use_case.execute(invitacion.token)

    async def test_invitacion_ya_usada_lanza_invitacion_ya_usada(self):
        invitacion_repo = FakeInvitacionRepository()
        comision_repo = FakeComisionRepository()
        materia_port = FakeMateriaPort()
        invitacion = Invitacion.crear(uuid.uuid4(), uuid.uuid4())
        invitacion.usada_en = datetime.now(UTC)
        await invitacion_repo.guardar(invitacion)

        use_case = ObtenerInvitacionUseCase(invitacion_repo, comision_repo, materia_port)

        with pytest.raises(InvitacionYaUsada):
            await use_case.execute(invitacion.token)
