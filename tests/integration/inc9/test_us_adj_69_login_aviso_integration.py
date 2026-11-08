"""`POST /identidad/login` avisa que queda 1 intento solo en el 2.º fallo (US-ADJ-69).

Requiere una base descartable (`DATABASE_URL` inline): `tests/integration/conftest.py` vacía las tablas.
"""

from __future__ import annotations

import uuid

from httpx import ASGITransport, AsyncClient, Response

from src.app import app
from src.identidad.entities.usuario import Usuario
from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher
from src.identidad.interface_adapters.gateways.usuario_repository import SQLAlchemyUsuarioRepository
from src.shared.entities.tipo_perfil import TipoPerfil

PASSWORD = "Docente#2026"
INCORRECTA = "otra-contraseña"
TEXTO = "Email o contraseña inválidos."


async def _login(email: str, password: str) -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post("/identidad/login", json={"email": email, "password": password})


async def _crear(session, tipo: TipoPerfil = TipoPerfil.DOCENTE) -> str:
    email = f"persona.{uuid.uuid4()}@fiuner.edu.ar"
    usuario = Usuario.crear("Persona", email, BcryptPasswordHasher().hash(PASSWORD), tipo)
    await SQLAlchemyUsuarioRepository(session).guardar(usuario)
    return email


class TestLoginAvisoUltimoIntento:
    """`POST /identidad/login` contra la base: el aviso va solo en el 2.º fallo."""

    async def test_solo_el_segundo_fallo_trae_el_aviso_y_el_cuarto_intento_es_403(self, session):
        """Secuencia completa de cuatro intentos fallidos sobre una cuenta existente."""
        email = await _crear(session)

        primero = await _login(email, INCORRECTA)
        segundo = await _login(email, INCORRECTA)
        tercero = await _login(email, INCORRECTA)
        cuarto = await _login(email, INCORRECTA)

        assert primero.status_code == 401
        assert primero.json()["detail"] == TEXTO
        assert segundo.status_code == 401
        assert segundo.json()["detail"] == {"mensaje": TEXTO, "intentos_restantes": 1}
        assert tercero.status_code == 401
        assert tercero.json()["detail"] == TEXTO
        assert cuarto.status_code == 403

    async def test_un_email_inexistente_nunca_recibe_el_aviso(self, session):
        """Tres intentos con un email inexistente responden siempre lo mismo."""
        email = f"no-existe.{uuid.uuid4()}@fiuner.edu.ar"

        respuestas = [await _login(email, INCORRECTA) for _ in range(3)]

        assert [r.status_code for r in respuestas] == [401, 401, 401]
        assert [r.json()["detail"] for r in respuestas] == [TEXTO, TEXTO, TEXTO]

    async def test_un_login_correcto_reinicia_el_contador(self, session):
        """Fallo, éxito y fallo: el segundo fallo de la tanda no avisa."""
        email = await _crear(session)
        await _login(email, INCORRECTA)

        correcto = await _login(email, PASSWORD)
        despues = await _login(email, INCORRECTA)

        assert correcto.status_code == 200
        assert despues.status_code == 401
        assert despues.json()["detail"] == TEXTO

    async def test_el_unico_administrador_tambien_recibe_el_aviso(self, session):
        """El único Administrador recibe el aviso en el 2.º fallo."""
        email = await _crear(session, TipoPerfil.ADMINISTRADOR)
        await _login(email, INCORRECTA)

        segundo = await _login(email, INCORRECTA)

        assert segundo.status_code == 401
        assert segundo.json()["detail"] == {"mensaje": TEXTO, "intentos_restantes": 1}
