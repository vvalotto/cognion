import uuid

from src.identidad.entities.comision import Comision
from src.identidad.entities.usuario import Estudiante, TipoPerfil, Usuario
from src.identidad.frameworks.db.models import UsuarioModel
from src.identidad.interface_adapters.gateways.comision_repository import (
    SQLAlchemyComisionRepository,
)
from src.identidad.interface_adapters.gateways.usuario_repository import SQLAlchemyUsuarioRepository


class TestSQLAlchemyUsuarioRepositoryIntegration:
    async def test_guardar_y_obtener_por_id(self, session):
        repo = SQLAlchemyUsuarioRepository(session)
        usuario = Usuario.crear("Ana", "ana@fiuner.edu.ar", "hash123", TipoPerfil.DOCENTE)

        await repo.guardar(usuario)
        recuperado = await repo.obtener_por_id(usuario.id)

        assert recuperado is not None
        assert recuperado.email == "ana@fiuner.edu.ar"
        assert recuperado.tipo_perfil == TipoPerfil.DOCENTE

    async def test_existe_email_true_despues_de_guardar(self, session):
        repo = SQLAlchemyUsuarioRepository(session)
        usuario = Usuario.crear("Ana", "ana2@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR)
        await repo.guardar(usuario)

        assert await repo.existe_email("ana2@fiuner.edu.ar") is True
        assert await repo.existe_email("nadie@fiuner.edu.ar") is False

    async def test_obtener_por_id_inexistente_retorna_none(self, session):
        repo = SQLAlchemyUsuarioRepository(session)

        assert await repo.obtener_por_id(uuid.uuid4()) is None

    async def test_obtener_por_id_con_usuario_sin_perfil_retorna_none(self, session):
        """Caso defensivo: fila `usuario` huérfana sin perfil asociado (no debería ocurrir
        vía la API pública, ver INV-ID-09, pero el gateway debe manejarlo sin romper)."""
        repo = SQLAlchemyUsuarioRepository(session)
        usuario_id = uuid.uuid4()
        session.add(
            UsuarioModel(
                id=usuario_id,
                nombre="Huérfano",
                email="huerfano@fiuner.edu.ar",
                password_hash="hash",
            )
        )
        await session.commit()

        assert await repo.obtener_por_id(usuario_id) is None

    async def test_obtener_por_email(self, session):
        repo = SQLAlchemyUsuarioRepository(session)
        usuario = Usuario.crear("Ana", "ana3@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE)
        await repo.guardar(usuario)

        recuperado = await repo.obtener_por_email("ana3@fiuner.edu.ar")

        assert recuperado is not None
        assert recuperado.id == usuario.id
        assert recuperado.tipo_perfil == TipoPerfil.DOCENTE

    async def test_obtener_por_email_inexistente_retorna_none(self, session):
        repo = SQLAlchemyUsuarioRepository(session)

        assert await repo.obtener_por_email("no-existe@fiuner.edu.ar") is None

    async def test_guardar_y_obtener_estudiante_con_comision(self, session):
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        comision_repo = SQLAlchemyComisionRepository(session)
        admin = Usuario.crear("Vic", "vic.est@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR)
        await usuario_repo.guardar(admin)
        comision = Comision.crear("IS", "lu 10-12", admin.id)
        await comision_repo.guardar(comision)

        estudiante = Usuario.crear_estudiante("Nico", "nico.est@fiuner.edu.ar", "hash", comision.id)
        await usuario_repo.guardar(estudiante)
        recuperado = await usuario_repo.obtener_por_id(estudiante.id)

        assert recuperado is not None
        assert isinstance(recuperado.perfil, Estudiante)
        assert recuperado.perfil.comision_id == comision.id
        assert recuperado.tipo_perfil == TipoPerfil.ESTUDIANTE
