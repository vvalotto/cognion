import uuid
from datetime import UTC, datetime

from src.identidad.entities.comision import Comision
from src.identidad.entities.invitacion import Invitacion
from src.identidad.entities.usuario import TipoPerfil, Usuario
from src.identidad.frameworks.db.models import InvitacionModel
from src.identidad.interface_adapters.gateways.comision_repository import (
    SQLAlchemyComisionRepository,
)
from src.identidad.interface_adapters.gateways.invitacion_repository import (
    SQLAlchemyInvitacionRepository,
)
from src.identidad.interface_adapters.gateways.usuario_repository import SQLAlchemyUsuarioRepository


async def _crear_invitacion(session) -> tuple[Invitacion, Comision]:
    """Prepara admin, docente, comisión e invitación persistidos para los tests."""
    usuario_repo = SQLAlchemyUsuarioRepository(session)
    comision_repo = SQLAlchemyComisionRepository(session)
    invitacion_repo = SQLAlchemyInvitacionRepository(session)

    admin = Usuario.crear(
        "Vic", f"vic.{uuid.uuid4()}@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR
    )
    await usuario_repo.guardar(admin)
    docente = Usuario.crear("Ana", f"ana.{uuid.uuid4()}@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE)
    await usuario_repo.guardar(docente)
    comision = Comision.crear("IS", "lu 10-12", admin.id)
    await comision_repo.guardar(comision)

    invitacion = Invitacion.crear(comision.id, docente.id)
    await invitacion_repo.guardar(invitacion)
    return invitacion, comision


class TestSQLAlchemyInvitacionRepositoryIntegration:
    async def test_guardar_persiste_invitacion(self, session):
        invitacion, comision = await _crear_invitacion(session)

        modelo = await session.get(InvitacionModel, invitacion.id)
        assert modelo is not None
        assert modelo.comision_id == comision.id
        assert modelo.docente_id == invitacion.docente_id
        assert modelo.token == invitacion.token
        assert modelo.usada_en is None

    async def test_obtener_por_token_encuentra_la_invitacion(self, session):
        invitacion, _comision = await _crear_invitacion(session)
        invitacion_repo = SQLAlchemyInvitacionRepository(session)

        encontrada = await invitacion_repo.obtener_por_token(invitacion.token)

        assert encontrada is not None
        assert encontrada.id == invitacion.id

    async def test_obtener_por_token_inexistente_retorna_none(self, session):
        invitacion_repo = SQLAlchemyInvitacionRepository(session)

        assert await invitacion_repo.obtener_por_token("token-inexistente") is None

    async def test_actualizar_persiste_usada_en(self, session):
        invitacion, _comision = await _crear_invitacion(session)
        invitacion_repo = SQLAlchemyInvitacionRepository(session)
        ahora = datetime.now(UTC)
        invitacion.aceptar(ahora)

        await invitacion_repo.actualizar(invitacion)

        modelo = await session.get(InvitacionModel, invitacion.id)
        assert modelo.usada_en == ahora
