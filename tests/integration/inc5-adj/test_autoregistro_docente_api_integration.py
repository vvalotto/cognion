import uuid

from httpx import ASGITransport, AsyncClient

from src.app import app


class TestAutoregistroDocenteAPIIntegration:
    async def test_autoregistro_exitoso_crea_docente_activo(self, session):
        email = f"docente.nuevo.{uuid.uuid4()}@fiuner.edu.ar"

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/identidad/autoregistro/docente",
                json={"nombre": "Nico Docente", "email": email, "password": "claveSegura1#"},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == email
        assert data["tipo_perfil"] == "docente"

    async def test_autoregistro_rechaza_email_ya_registrado(self, session):
        email = f"docente.duplicado.{uuid.uuid4()}@fiuner.edu.ar"

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            primera = await client.post(
                "/identidad/autoregistro/docente",
                json={"nombre": "Nico", "email": email, "password": "claveSegura1#"},
            )
            assert primera.status_code == 201

            segunda = await client.post(
                "/identidad/autoregistro/docente",
                json={"nombre": "Otro", "email": email, "password": "claveSegura2#"},
            )

        assert segunda.status_code == 409

    async def test_autoregistro_rechaza_password_debil(self, session):
        email = f"docente.debil.{uuid.uuid4()}@fiuner.edu.ar"

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/identidad/autoregistro/docente",
                json={"nombre": "Nico", "email": email, "password": "abc123"},
            )

        assert response.status_code == 422

    async def test_docente_autoregistrado_puede_loguearse_de_inmediato(self, session):
        email = f"docente.login.{uuid.uuid4()}@fiuner.edu.ar"

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            crear = await client.post(
                "/identidad/autoregistro/docente",
                json={"nombre": "Nico", "email": email, "password": "claveSegura1#"},
            )
            assert crear.status_code == 201

            login = await client.post(
                "/identidad/login", json={"email": email, "password": "claveSegura1#"}
            )

        assert login.status_code == 200
        assert login.json()["rol"] == "docente"
