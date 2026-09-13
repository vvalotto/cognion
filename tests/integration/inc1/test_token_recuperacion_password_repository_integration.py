import uuid
from datetime import UTC, datetime

from src.identidad.entities.token_recuperacion_password import TokenRecuperacionPassword
from src.identidad.entities.usuario import Usuario
from src.identidad.frameworks.db.models import TokenRecuperacionPasswordModel
from src.identidad.interface_adapters.gateways.token_recuperacion_password_repository import (
    SQLAlchemyTokenRecuperacionPasswordRepository,
)
from src.identidad.interface_adapters.gateways.usuario_repository import SQLAlchemyUsuarioRepository
from src.shared.entities.tipo_perfil import TipoPerfil


async def _crear_usuario(session) -> Usuario:
    usuario_repo = SQLAlchemyUsuarioRepository(session)
    usuario = Usuario.crear(
        "Ana", f"ana.{uuid.uuid4()}@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE
    )
    await usuario_repo.guardar(usuario)
    return usuario


class TestSQLAlchemyTokenRecuperacionPasswordRepositoryIntegration:
    async def test_guardar_persiste_token(self, session):
        usuario = await _crear_usuario(session)
        token_repo = SQLAlchemyTokenRecuperacionPasswordRepository(session)
        token = TokenRecuperacionPassword.crear(usuario.id)

        await token_repo.guardar(token)

        modelo = await session.get(TokenRecuperacionPasswordModel, token.id)
        assert modelo is not None
        assert modelo.usuario_id == usuario.id
        assert modelo.token == token.token
        assert modelo.usado_en is None

    async def test_obtener_por_token_encuentra_el_token(self, session):
        usuario = await _crear_usuario(session)
        token_repo = SQLAlchemyTokenRecuperacionPasswordRepository(session)
        token = TokenRecuperacionPassword.crear(usuario.id)
        await token_repo.guardar(token)

        encontrado = await token_repo.obtener_por_token(token.token)

        assert encontrado is not None
        assert encontrado.id == token.id

    async def test_obtener_por_token_inexistente_retorna_none(self, session):
        token_repo = SQLAlchemyTokenRecuperacionPasswordRepository(session)

        assert await token_repo.obtener_por_token("token-inexistente") is None

    async def test_actualizar_persiste_usado_en(self, session):
        usuario = await _crear_usuario(session)
        token_repo = SQLAlchemyTokenRecuperacionPasswordRepository(session)
        token = TokenRecuperacionPassword.crear(usuario.id)
        await token_repo.guardar(token)
        ahora = datetime.now(UTC)
        token.invalidar(ahora)

        await token_repo.actualizar(token)

        modelo = await session.get(TokenRecuperacionPasswordModel, token.id)
        assert modelo.usado_en == ahora

    async def test_invalidar_activos_de_marca_solo_los_tokens_sin_usar_del_usuario(self, session):
        usuario = await _crear_usuario(session)
        otro_usuario = await _crear_usuario(session)
        token_repo = SQLAlchemyTokenRecuperacionPasswordRepository(session)

        activo = TokenRecuperacionPassword.crear(usuario.id)
        await token_repo.guardar(activo)
        de_otro_usuario = TokenRecuperacionPassword.crear(otro_usuario.id)
        await token_repo.guardar(de_otro_usuario)

        ahora = datetime.now(UTC)
        await token_repo.invalidar_activos_de(usuario.id, ahora)

        modelo_activo = await session.get(TokenRecuperacionPasswordModel, activo.id)
        modelo_otro = await session.get(TokenRecuperacionPasswordModel, de_otro_usuario.id)
        assert modelo_activo.usado_en == ahora
        assert modelo_otro.usado_en is None

    async def test_invalidar_activos_de_no_toca_tokens_ya_usados(self, session):
        usuario = await _crear_usuario(session)
        token_repo = SQLAlchemyTokenRecuperacionPasswordRepository(session)
        ya_usado = TokenRecuperacionPassword.crear(usuario.id)
        primer_instante = datetime.now(UTC)
        ya_usado.invalidar(primer_instante)
        await token_repo.guardar(ya_usado)

        segundo_instante = datetime.now(UTC)
        await token_repo.invalidar_activos_de(usuario.id, segundo_instante)

        modelo = await session.get(TokenRecuperacionPasswordModel, ya_usado.id)
        assert modelo.usado_en == primer_instante
