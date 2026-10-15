"""US-ADJ-59 — `POST /identidad/login` sobre una cuenta deshabilitada (INV-ID-18)."""

import uuid

from httpx import ASGITransport, AsyncClient

from src.app import app
from src.identidad.entities.usuario import Usuario
from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher
from src.identidad.interface_adapters.gateways.usuario_repository import SQLAlchemyUsuarioRepository
from src.shared.entities.tipo_perfil import TipoPerfil

PASSWORD = "Docente#2026"


async def _crear_docente(session, **campos: object) -> Usuario:
    email = f"docente.{uuid.uuid4()}@fiuner.edu.ar"
    usuario = Usuario.crear(
        "Docente", email, BcryptPasswordHasher().hash(PASSWORD), TipoPerfil.DOCENTE
    )
    repo = SQLAlchemyUsuarioRepository(session)
    await repo.guardar(usuario)
    if campos:
        # `guardar()` no persiste `deshabilitada`/`bloqueada`/contadores: solo `actualizar()`.
        for campo, valor in campos.items():
            setattr(usuario, campo, valor)
        await repo.actualizar(usuario)
    return usuario


async def _login(email: str, password: str):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post("/identidad/login", json={"email": email, "password": password})


class TestLoginCuentaDeshabilitadaAPIIntegration:
    async def test_contrasena_correcta_responde_403_estructurado_sin_token(self, session):
        usuario = await _crear_docente(session, deshabilitada=True)

        response = await _login(usuario.email, PASSWORD)

        assert response.status_code == 403
        detail = response.json()["detail"]
        assert detail["codigo"] == "cuenta_deshabilitada"
        assert "deshabilitada" in detail["mensaje"]
        assert "access_token" not in response.json()

    async def test_el_rechazo_no_depende_de_la_contrasena_ni_consume_intentos(self, session):
        usuario = await _crear_docente(session, deshabilitada=True)

        response = await _login(usuario.email, "una-contrasena-incorrecta")

        assert response.status_code == 403
        assert response.json()["detail"]["codigo"] == "cuenta_deshabilitada"
        repo = SQLAlchemyUsuarioRepository(session)
        recargado = await repo.obtener_por_id(usuario.id)
        assert recargado is not None
        assert recargado.intentos_fallidos_login == 0
        assert recargado.bloqueada is False

    async def test_deshabilitada_y_bloqueada_a_la_vez_gana_deshabilitada(self, session):
        usuario = await _crear_docente(
            session, deshabilitada=True, bloqueada=True, intentos_fallidos_login=3
        )

        response = await _login(usuario.email, PASSWORD)

        assert response.status_code == 403
        assert response.json()["detail"]["codigo"] == "cuenta_deshabilitada"

    async def test_reactivar_la_cuenta_restituye_el_acceso(self, session):
        usuario = await _crear_docente(session, deshabilitada=True)
        usuario.activar()
        await SQLAlchemyUsuarioRepository(session).actualizar(usuario)

        response = await _login(usuario.email, PASSWORD)

        assert response.status_code == 200
        assert response.json()["rol"] == "docente"

    async def test_una_cuenta_activa_no_cambia_de_comportamiento(self, session):
        usuario = await _crear_docente(session)

        response = await _login(usuario.email, PASSWORD)

        assert response.status_code == 200
        assert response.json()["token_type"] == "bearer"

    async def test_una_cuenta_bloqueada_conserva_el_detail_en_texto_plano(self, session):
        usuario = await _crear_docente(session, bloqueada=True, intentos_fallidos_login=3)

        response = await _login(usuario.email, PASSWORD)

        assert response.status_code == 403
        assert isinstance(response.json()["detail"], str)
        assert "bloqueada" in response.json()["detail"]
