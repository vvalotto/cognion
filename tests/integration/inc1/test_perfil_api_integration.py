import uuid

from httpx import ASGITransport, AsyncClient

from src.app import app
from src.identidad.entities.usuario import Usuario
from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher
from src.identidad.interface_adapters.gateways.usuario_repository import (
    SQLAlchemyUsuarioRepository,
)
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.security.jwt_pyjwt import PyJWTIssuer


def _headers_para(usuario: Usuario) -> dict[str, str]:
    jwt_vo = PyJWTIssuer().emitir(usuario.id, usuario.tipo_perfil)
    return {"Authorization": f"Bearer {jwt_vo.token}"}


class TestCambiarPasswordAPIIntegration:
    """US-2.2.5: cambio de la propia contraseña, self-service."""

    async def test_cambio_exitoso_devuelve_204(self, session):
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        hasher = BcryptPasswordHasher()
        usuario = Usuario.crear(
            "Docente Propio",
            f"docente.propio.{uuid.uuid4()}@fiuner.edu.ar",
            hasher.hash("claveActual1"),
            TipoPerfil.DOCENTE,
        )
        await usuario_repo.guardar(usuario)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                "/usuarios/me/password",
                json={"password_actual": "claveActual1", "password_nueva": "claveNueva123"},
                headers=_headers_para(usuario),
            )

        assert response.status_code == 204

    async def test_password_cambiada_habilita_login_con_la_nueva(self, session):
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        hasher = BcryptPasswordHasher()
        email = f"login.propio.{uuid.uuid4()}@fiuner.edu.ar"
        usuario = Usuario.crear(
            "Docente Login", email, hasher.hash("claveActual1"), TipoPerfil.DOCENTE
        )
        await usuario_repo.guardar(usuario)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.put(
                "/usuarios/me/password",
                json={"password_actual": "claveActual1", "password_nueva": "claveNueva123"},
                headers=_headers_para(usuario),
            )
            response = await client.post(
                "/identidad/login", json={"email": email, "password": "claveNueva123"}
            )

        assert response.status_code == 200
        assert "access_token" in response.json()

    async def test_password_actual_incorrecta_devuelve_401(self, session):
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        hasher = BcryptPasswordHasher()
        usuario = Usuario.crear(
            "Docente Fallo",
            f"docente.fallo.{uuid.uuid4()}@fiuner.edu.ar",
            hasher.hash("claveActual1"),
            TipoPerfil.DOCENTE,
        )
        await usuario_repo.guardar(usuario)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                "/usuarios/me/password",
                json={"password_actual": "incorrecta", "password_nueva": "claveNueva123"},
                headers=_headers_para(usuario),
            )

        assert response.status_code == 401

    async def test_tercer_fallo_consecutivo_bloquea_y_devuelve_401(self, session):
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        hasher = BcryptPasswordHasher()
        usuario = Usuario.crear(
            "Docente Bloqueo",
            f"docente.bloqueo.{uuid.uuid4()}@fiuner.edu.ar",
            hasher.hash("claveActual1"),
            TipoPerfil.DOCENTE,
        )
        await usuario_repo.guardar(usuario)
        headers = _headers_para(usuario)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for _ in range(3):
                response = await client.put(
                    "/usuarios/me/password",
                    json={"password_actual": "incorrecta", "password_nueva": "claveNueva123"},
                    headers=headers,
                )

        assert response.status_code == 401
        actualizado = await usuario_repo.obtener_por_id(usuario.id)
        assert actualizado is not None
        assert actualizado.bloqueada is True

    async def test_cuenta_ya_bloqueada_devuelve_403(self, session):
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        hasher = BcryptPasswordHasher()
        usuario = Usuario.crear(
            "Docente Ya Bloqueado",
            f"docente.yabloqueado.{uuid.uuid4()}@fiuner.edu.ar",
            hasher.hash("claveActual1"),
            TipoPerfil.DOCENTE,
        )
        await usuario_repo.guardar(usuario)
        usuario.bloqueada = True
        await usuario_repo.actualizar(usuario)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                "/usuarios/me/password",
                json={"password_actual": "claveActual1", "password_nueva": "claveNueva123"},
                headers=_headers_para(usuario),
            )

        assert response.status_code == 403

    async def test_password_nueva_demasiado_corta_devuelve_422(self, session):
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        hasher = BcryptPasswordHasher()
        usuario = Usuario.crear(
            "Docente Corta",
            f"docente.corta.{uuid.uuid4()}@fiuner.edu.ar",
            hasher.hash("claveActual1"),
            TipoPerfil.DOCENTE,
        )
        await usuario_repo.guardar(usuario)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                "/usuarios/me/password",
                json={"password_actual": "claveActual1", "password_nueva": "corta"},
                headers=_headers_para(usuario),
            )

        assert response.status_code == 422

    async def test_sin_autenticacion_devuelve_401(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                "/usuarios/me/password",
                json={"password_actual": "claveActual1", "password_nueva": "claveNueva123"},
            )

        assert response.status_code == 401
