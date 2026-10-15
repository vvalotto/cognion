"""US-ADJ-62 — `POST /identidad/recuperar-password/confirmar` desbloquea la cuenta."""

import uuid
from datetime import UTC, datetime, timedelta

from httpx import ASGITransport, AsyncClient

from src.app import app
from src.identidad.entities.token_recuperacion_password import TokenRecuperacionPassword
from src.identidad.entities.usuario import Usuario
from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher
from src.identidad.interface_adapters.gateways.token_recuperacion_password_repository import (
    SQLAlchemyTokenRecuperacionPasswordRepository,
)
from src.identidad.interface_adapters.gateways.usuario_repository import SQLAlchemyUsuarioRepository
from src.shared.entities.tipo_perfil import TipoPerfil

PASSWORD_VIEJA = "Docente#2026"
PASSWORD_NUEVA = "Segura#2026x"


async def _crear_usuario(session, perfil: TipoPerfil = TipoPerfil.DOCENTE, **campos: object):
    email = f"cuenta.{uuid.uuid4()}@fiuner.edu.ar"
    usuario = Usuario.crear("Cuenta", email, BcryptPasswordHasher().hash(PASSWORD_VIEJA), perfil)
    repo = SQLAlchemyUsuarioRepository(session)
    await repo.guardar(usuario)
    if campos:
        for campo, valor in campos.items():
            setattr(usuario, campo, valor)
        await repo.actualizar(usuario)
    return usuario


async def _crear_token(session, usuario: Usuario) -> TokenRecuperacionPassword:
    token = TokenRecuperacionPassword.crear(usuario.id)
    await SQLAlchemyTokenRecuperacionPasswordRepository(session).guardar(token)
    return token


async def _post(path: str, json: dict):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(path, json=json)


async def _confirmar(token: str, password: str = PASSWORD_NUEVA):
    return await _post(
        "/identidad/recuperar-password/confirmar", {"token": token, "password_nueva": password}
    )


async def _recargar(session, usuario: Usuario) -> Usuario:
    session.expire_all()
    recargado = await SQLAlchemyUsuarioRepository(session).obtener_por_id(usuario.id)
    assert recargado is not None
    return recargado


class TestRecuperarPasswordDesbloqueaAPIIntegration:
    async def test_desbloquea_una_cuenta_bloqueada_y_resetea_contadores(self, session):
        usuario = await _crear_usuario(
            session, bloqueada=True, intentos_fallidos_login=3, intentos_fallidos_password=2
        )
        token = await _crear_token(session, usuario)

        response = await _confirmar(token.token)

        assert response.status_code == 200
        recargado = await _recargar(session, usuario)
        assert recargado.bloqueada is False
        assert recargado.intentos_fallidos_login == 0
        assert recargado.intentos_fallidos_password == 0

    async def test_tras_recuperar_el_login_con_la_contrasena_nueva_responde_200(self, session):
        usuario = await _crear_usuario(session, bloqueada=True, intentos_fallidos_login=3)
        token = await _crear_token(session, usuario)
        await _confirmar(token.token)

        response = await _post(
            "/identidad/login", {"email": usuario.email, "password": PASSWORD_NUEVA}
        )

        assert response.status_code == 200
        assert response.json()["access_token"]

    async def test_libera_al_administrador_bloqueado_temporalmente(self, session):
        admin = await _crear_usuario(
            session,
            TipoPerfil.ADMINISTRADOR,
            bloqueada=True,
            bloqueada_hasta=datetime.now(UTC) + timedelta(minutes=10),
        )
        token = await _crear_token(session, admin)

        response = await _confirmar(token.token)

        assert response.status_code == 200
        recargado = await _recargar(session, admin)
        assert recargado.bloqueada is False
        assert recargado.bloqueada_hasta is None

    async def test_no_reactiva_una_cuenta_deshabilitada(self, session):
        usuario = await _crear_usuario(session, deshabilitada=True)
        token = await _crear_token(session, usuario)

        await _confirmar(token.token)

        recargado = await _recargar(session, usuario)
        assert recargado.deshabilitada is True
        login = await _post(
            "/identidad/login", {"email": usuario.email, "password": PASSWORD_NUEVA}
        )
        assert login.status_code == 403
        assert login.json()["detail"]["codigo"] == "cuenta_deshabilitada"

    async def test_token_vencido_no_desbloquea(self, session):
        usuario = await _crear_usuario(session, bloqueada=True, intentos_fallidos_login=3)
        token = TokenRecuperacionPassword.crear(usuario.id)
        token.expira_en = datetime.now(UTC) - timedelta(seconds=1)
        await SQLAlchemyTokenRecuperacionPasswordRepository(session).guardar(token)

        response = await _confirmar(token.token)

        assert response.status_code == 422
        assert (await _recargar(session, usuario)).bloqueada is True

    async def test_password_que_no_cumple_la_politica_no_desbloquea(self, session):
        usuario = await _crear_usuario(session, bloqueada=True, intentos_fallidos_login=3)
        token = await _crear_token(session, usuario)

        response = await _confirmar(token.token, "Corta#1")

        assert response.status_code == 422
        assert (await _recargar(session, usuario)).bloqueada is True
