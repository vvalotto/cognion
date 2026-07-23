import uuid

import jwt as pyjwt
from httpx import ASGITransport, AsyncClient

from src.app import app
from src.identidad.entities.usuario import TipoPerfil, Usuario
from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher
from src.identidad.interface_adapters.gateways.usuario_repository import SQLAlchemyUsuarioRepository
from src.settings import settings


class TestAuthAPIIntegration:
    async def test_login_exitoso_docente(self, session):
        hasher = BcryptPasswordHasher()
        repo = SQLAlchemyUsuarioRepository(session)
        email = f"docente.{uuid.uuid4()}@fiuner.edu.ar"
        usuario = Usuario.crear(
            "Docente", email, hasher.hash("Docente#2026"), TipoPerfil.DOCENTE
        )
        await repo.guardar(usuario)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/identidad/login", json={"email": email, "password": "Docente#2026"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["rol"] == "docente"
        assert data["token_type"] == "bearer"

        payload = pyjwt.decode(
            data["access_token"], settings.secret_key, algorithms=[settings.algorithm]
        )
        assert payload["sub"] == str(usuario.id)
        assert payload["rol"] == "docente"

    async def test_login_exitoso_administrador(self, session):
        hasher = BcryptPasswordHasher()
        repo = SQLAlchemyUsuarioRepository(session)
        email = f"admin.{uuid.uuid4()}@fiuner.edu.ar"
        usuario = Usuario.crear(
            "Admin", email, hasher.hash("Admin#2026"), TipoPerfil.ADMINISTRADOR
        )
        await repo.guardar(usuario)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/identidad/login", json={"email": email, "password": "Admin#2026"}
            )

        assert response.status_code == 200
        assert response.json()["rol"] == "administrador"

    async def test_login_exitoso_estudiante(self, session):
        from src.identidad.entities.comision import Comision
        from src.identidad.interface_adapters.gateways.comision_repository import (
            SQLAlchemyComisionRepository,
        )

        hasher = BcryptPasswordHasher()
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        comision_repo = SQLAlchemyComisionRepository(session)
        admin = Usuario.crear(
            "Vic", f"vic.{uuid.uuid4()}@fiuner.edu.ar", hasher.hash("x"), TipoPerfil.ADMINISTRADOR
        )
        await usuario_repo.guardar(admin)
        comision = Comision.crear("IS-2026-C1", "lu 10-12", admin.id)
        await comision_repo.guardar(comision)

        email = f"estudiante.{uuid.uuid4()}@fiuner.edu.ar"
        estudiante = Usuario.crear_estudiante(
            "Estudiante", email, hasher.hash("Estudiante#2026"), comision.id
        )
        await usuario_repo.guardar(estudiante)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/identidad/login", json={"email": email, "password": "Estudiante#2026"}
            )

        assert response.status_code == 200
        assert response.json()["rol"] == "estudiante"

    async def test_login_rechaza_password_incorrecta(self, session):
        hasher = BcryptPasswordHasher()
        repo = SQLAlchemyUsuarioRepository(session)
        email = f"docente.{uuid.uuid4()}@fiuner.edu.ar"
        usuario = Usuario.crear("Docente", email, hasher.hash("Docente#2026"), TipoPerfil.DOCENTE)
        await repo.guardar(usuario)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/identidad/login", json={"email": email, "password": "incorrecta"}
            )

        assert response.status_code == 401

    async def test_login_rechaza_email_inexistente_con_el_mismo_mensaje(self, session):
        hasher = BcryptPasswordHasher()
        repo = SQLAlchemyUsuarioRepository(session)
        email = f"docente.{uuid.uuid4()}@fiuner.edu.ar"
        usuario = Usuario.crear("Docente", email, hasher.hash("Docente#2026"), TipoPerfil.DOCENTE)
        await repo.guardar(usuario)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            respuesta_password_incorrecta = await client.post(
                "/identidad/login", json={"email": email, "password": "incorrecta"}
            )
            respuesta_email_inexistente = await client.post(
                "/identidad/login",
                json={"email": "no-existe@fiuner.edu.ar", "password": "cualquiera"},
            )

        assert respuesta_password_incorrecta.status_code == 401
        assert respuesta_email_inexistente.status_code == 401
        assert (
            respuesta_password_incorrecta.json()["detail"]
            == respuesta_email_inexistente.json()["detail"]
        )
