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


class TestSQLAlchemyInvitacionRepositoryIntegration:
    async def test_guardar_persiste_invitacion(self, session):
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        comision_repo = SQLAlchemyComisionRepository(session)
        invitacion_repo = SQLAlchemyInvitacionRepository(session)

        admin = Usuario.crear("Vic", "vic.inv@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR)
        await usuario_repo.guardar(admin)
        docente = Usuario.crear("Ana", "ana.inv@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE)
        await usuario_repo.guardar(docente)
        comision = Comision.crear("IS", "lu 10-12", admin.id)
        await comision_repo.guardar(comision)

        invitacion = Invitacion.crear(comision.id, docente.id)
        await invitacion_repo.guardar(invitacion)

        modelo = await session.get(InvitacionModel, invitacion.id)
        assert modelo is not None
        assert modelo.comision_id == comision.id
        assert modelo.docente_id == docente.id
        assert modelo.token == invitacion.token
        assert modelo.usada_en is None
