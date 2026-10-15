"""US-ADJ-60 — baja y bloqueo del último Administrador operativo contra la base real."""

import uuid
from datetime import UTC, datetime, timedelta

from httpx import ASGITransport, AsyncClient

from src.app import app
from src.identidad.entities.usuario import Usuario
from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher
from src.identidad.interface_adapters.gateways.usuario_repository import SQLAlchemyUsuarioRepository
from src.shared.entities.tipo_perfil import TipoPerfil

PASSWORD = "Admin#2026-ok"


async def _crear(session, perfil: TipoPerfil, **campos: object) -> Usuario:
    usuario = Usuario.crear(
        "Cuenta", f"c.{uuid.uuid4()}@fiuner.edu.ar", BcryptPasswordHasher().hash(PASSWORD), perfil
    )
    repo = SQLAlchemyUsuarioRepository(session)
    await repo.guardar(usuario)
    if campos:
        for campo, valor in campos.items():
            setattr(usuario, campo, valor)
        await repo.actualizar(usuario)
    return usuario


async def _request(metodo: str, path: str, **kwargs):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.request(metodo, path, **kwargs)


async def _login(email: str, password: str):
    return await _request("POST", "/identidad/login", json={"email": email, "password": password})


class TestContarAdministradoresOperativos:
    async def test_solo_cuenta_administradores_ni_deshabilitados_ni_bloqueados(self, session):
        a = await _crear(session, TipoPerfil.ADMINISTRADOR)
        await _crear(session, TipoPerfil.ADMINISTRADOR)
        await _crear(session, TipoPerfil.ADMINISTRADOR, deshabilitada=True)
        await _crear(session, TipoPerfil.ADMINISTRADOR, bloqueada=True)
        await _crear(session, TipoPerfil.DOCENTE)
        repo = SQLAlchemyUsuarioRepository(session)

        assert await repo.contar_administradores_operativos() == 2
        assert await repo.contar_administradores_operativos(excluyendo=a.id) == 1

    async def test_bloqueada_hasta_se_persiste_y_se_lee(self, session):
        hasta = datetime.now(UTC) + timedelta(minutes=15)
        a = await _crear(session, TipoPerfil.ADMINISTRADOR, bloqueada=True, bloqueada_hasta=hasta)

        recargado = await SQLAlchemyUsuarioRepository(session).obtener_por_id(a.id)

        assert recargado is not None
        assert recargado.bloqueada_hasta == hasta


class TestBajaDeAdministradorAPI:
    async def test_con_otro_operativo_es_baja_logica_200(self, session, admin_headers):
        a = await _crear(session, TipoPerfil.ADMINISTRADOR)
        await _crear(session, TipoPerfil.ADMINISTRADOR)

        respuesta = await _request("DELETE", f"/usuarios/{a.id}", headers=admin_headers)

        assert respuesta.status_code == 200
        recargado = await SQLAlchemyUsuarioRepository(session).obtener_por_id(a.id)
        assert recargado is not None and recargado.deshabilitada is True

    async def test_el_ultimo_operativo_responde_409_estructurado(self, session, admin_headers):
        a = await _crear(session, TipoPerfil.ADMINISTRADOR)

        respuesta = await _request("DELETE", f"/usuarios/{a.id}", headers=admin_headers)

        assert respuesta.status_code == 409
        assert respuesta.json()["detail"]["codigo"] == "ultimo_administrador_operativo"
        recargado = await SQLAlchemyUsuarioRepository(session).obtener_por_id(a.id)
        assert recargado is not None and recargado.deshabilitada is False

    async def test_otro_bloqueado_no_cuenta_como_operativo(self, session, admin_headers):
        a = await _crear(session, TipoPerfil.ADMINISTRADOR)
        await _crear(session, TipoPerfil.ADMINISTRADOR, bloqueada=True)

        respuesta = await _request("DELETE", f"/usuarios/{a.id}", headers=admin_headers)

        assert respuesta.status_code == 409

    async def test_ya_deshabilitado_es_idempotente(self, session, admin_headers):
        a = await _crear(session, TipoPerfil.ADMINISTRADOR, deshabilitada=True)
        await _crear(session, TipoPerfil.ADMINISTRADOR)

        respuesta = await _request("DELETE", f"/usuarios/{a.id}", headers=admin_headers)

        assert respuesta.status_code == 200


class TestBloqueoTemporalLoginAPI:
    async def test_tres_fallos_del_ultimo_administrador_bloquean_por_15_minutos(self, session):
        a = await _crear(session, TipoPerfil.ADMINISTRADOR)
        for _ in range(3):
            assert (await _login(a.email, "incorrecta")).status_code in (401,)

        recargado = await SQLAlchemyUsuarioRepository(session).obtener_por_id(a.id)
        assert recargado is not None and recargado.bloqueada is True
        assert recargado.bloqueada_hasta is not None
        restante = recargado.bloqueada_hasta - datetime.now(UTC)
        assert timedelta(minutes=14) < restante <= timedelta(minutes=15)

        respuesta = await _login(a.email, PASSWORD)
        assert respuesta.status_code == 403
        detail = respuesta.json()["detail"]
        assert detail["codigo"] == "cuenta_bloqueada_temporal"
        assert detail["reintentar_en_segundos"] > 0

    async def test_el_bloqueo_vencido_se_levanta_solo(self, session):
        a = await _crear(
            session,
            TipoPerfil.ADMINISTRADOR,
            bloqueada=True,
            intentos_fallidos_login=3,
            bloqueada_hasta=datetime.now(UTC) - timedelta(seconds=1),
        )

        respuesta = await _login(a.email, PASSWORD)

        assert respuesta.status_code == 200
        recargado = await SQLAlchemyUsuarioRepository(session).obtener_por_id(a.id)
        assert recargado is not None
        assert recargado.bloqueada is False and recargado.bloqueada_hasta is None

    async def test_con_otro_administrador_el_bloqueo_es_permanente(self, session):
        a = await _crear(session, TipoPerfil.ADMINISTRADOR)
        await _crear(session, TipoPerfil.ADMINISTRADOR)
        for _ in range(3):
            await _login(a.email, "incorrecta")

        respuesta = await _login(a.email, PASSWORD)

        assert respuesta.status_code == 403
        assert isinstance(respuesta.json()["detail"], str)
        recargado = await SQLAlchemyUsuarioRepository(session).obtener_por_id(a.id)
        assert recargado is not None and recargado.bloqueada_hasta is None

    async def test_docente_conserva_el_bloqueo_permanente(self, session):
        d = await _crear(session, TipoPerfil.DOCENTE)
        for _ in range(3):
            await _login(d.email, "incorrecta")

        recargado = await SQLAlchemyUsuarioRepository(session).obtener_por_id(d.id)
        assert recargado is not None
        assert recargado.bloqueada is True and recargado.bloqueada_hasta is None


class TestBloqueoTemporalCambioPasswordAPI:
    async def test_tres_fallos_del_ultimo_administrador_bloquean_temporalmente(self, session):
        a = await _crear(session, TipoPerfil.ADMINISTRADOR)
        token = (await _login(a.email, PASSWORD)).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        cuerpo = {"password_actual": "incorrecta", "password_nueva": "Nueva#Pass2026"}

        for _ in range(3):
            await _request("PUT", "/usuarios/me/password", json=cuerpo, headers=headers)

        recargado = await SQLAlchemyUsuarioRepository(session).obtener_por_id(a.id)
        assert recargado is not None and recargado.bloqueada is True
        assert recargado.bloqueada_hasta is not None
        respuesta = await _request("PUT", "/usuarios/me/password", json=cuerpo, headers=headers)
        assert respuesta.status_code == 403
        assert respuesta.json()["detail"]["codigo"] == "cuenta_bloqueada_temporal"


class TestResetearPasswordLimpiaBloqueoTemporalAPI:
    async def test_el_reseteo_deja_bloqueada_hasta_en_null(self, session, admin_headers):
        a = await _crear(
            session,
            TipoPerfil.ADMINISTRADOR,
            bloqueada=True,
            bloqueada_hasta=datetime.now(UTC) + timedelta(minutes=10),
        )

        respuesta = await _request(
            "POST",
            f"/usuarios/{a.id}/resetear-password",
            json={"password_nueva": "Reseteada#2026"},
            headers=admin_headers,
        )

        assert respuesta.status_code in (200, 204)
        recargado = await SQLAlchemyUsuarioRepository(session).obtener_por_id(a.id)
        assert recargado is not None
        assert recargado.bloqueada is False and recargado.bloqueada_hasta is None
