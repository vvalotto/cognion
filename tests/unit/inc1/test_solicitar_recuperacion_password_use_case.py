import uuid

from src.identidad.entities.usuario import Docente, Usuario
from src.identidad.use_cases.solicitar_recuperacion_password import (
    SolicitarRecuperacionPasswordUseCase,
)
from tests.unit.inc1._fakes import (
    FakeCanalRecuperacion,
    FakeTokenRecuperacionPasswordRepository,
    FakeUsuarioRepository,
)


def _usuario(email: str) -> Usuario:
    usuario_id = uuid.uuid4()
    return Usuario(
        id=usuario_id,
        nombre="Docente de Prueba",
        email=email,
        password_hash="hash",
        perfil=Docente(id=usuario_id),
    )


class TestSolicitarRecuperacionPasswordUseCase:
    async def test_genera_token_para_email_de_cuenta_existente(self):
        usuario_repo = FakeUsuarioRepository()
        token_repo = FakeTokenRecuperacionPasswordRepository()
        canal = FakeCanalRecuperacion()
        usuario = _usuario("docente@fiuner.edu.ar")
        await usuario_repo.guardar(usuario)

        use_case = SolicitarRecuperacionPasswordUseCase(usuario_repo, token_repo, canal)
        await use_case.execute("docente@fiuner.edu.ar")

        tokens_del_usuario = [t for t in token_repo.tokens.values() if t.usuario_id == usuario.id]
        assert len(tokens_del_usuario) == 1
        assert tokens_del_usuario[0].usado_en is None

    async def test_envia_email_al_usuario_encontrado(self):
        usuario_repo = FakeUsuarioRepository()
        token_repo = FakeTokenRecuperacionPasswordRepository()
        canal = FakeCanalRecuperacion()
        usuario = _usuario("docente@fiuner.edu.ar")
        await usuario_repo.guardar(usuario)

        use_case = SolicitarRecuperacionPasswordUseCase(usuario_repo, token_repo, canal)
        await use_case.execute("docente@fiuner.edu.ar")

        assert len(canal.enviados) == 1
        email_enviado, token_enviado = canal.enviados[0]
        assert email_enviado == "docente@fiuner.edu.ar"
        token_generado = next(iter(token_repo.tokens.values()))
        assert token_enviado == token_generado.token

    async def test_email_inexistente_no_crea_token_ni_envia_email(self):
        usuario_repo = FakeUsuarioRepository()
        token_repo = FakeTokenRecuperacionPasswordRepository()
        canal = FakeCanalRecuperacion()

        use_case = SolicitarRecuperacionPasswordUseCase(usuario_repo, token_repo, canal)
        await use_case.execute("inexistente@fiuner.edu.ar")

        assert token_repo.tokens == {}
        assert canal.enviados == []

    async def test_solicitar_dos_veces_invalida_el_token_anterior(self):
        usuario_repo = FakeUsuarioRepository()
        token_repo = FakeTokenRecuperacionPasswordRepository()
        canal = FakeCanalRecuperacion()
        usuario = _usuario("docente@fiuner.edu.ar")
        await usuario_repo.guardar(usuario)
        use_case = SolicitarRecuperacionPasswordUseCase(usuario_repo, token_repo, canal)

        await use_case.execute("docente@fiuner.edu.ar")
        primer_token = next(iter(token_repo.tokens.values()))

        await use_case.execute("docente@fiuner.edu.ar")

        assert primer_token.usado_en is not None
        tokens_sin_usar = [t for t in token_repo.tokens.values() if t.usado_en is None]
        assert len(tokens_sin_usar) == 1
        assert tokens_sin_usar[0].token != primer_token.token

    async def test_fallo_de_envio_no_bloquea_ni_impide_la_creacion_del_token(self):
        usuario_repo = FakeUsuarioRepository()
        token_repo = FakeTokenRecuperacionPasswordRepository()
        canal = FakeCanalRecuperacion(falla=True)
        usuario = _usuario("docente@fiuner.edu.ar")
        await usuario_repo.guardar(usuario)

        use_case = SolicitarRecuperacionPasswordUseCase(usuario_repo, token_repo, canal)
        await use_case.execute("docente@fiuner.edu.ar")

        tokens_del_usuario = [t for t in token_repo.tokens.values() if t.usuario_id == usuario.id]
        assert len(tokens_del_usuario) == 1
        assert canal.enviados == []
