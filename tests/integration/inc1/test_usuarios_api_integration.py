from httpx import ASGITransport, AsyncClient

from src.app import app


class TestUsuariosAPIIntegration:
    async def test_crear_usuario_devuelve_201(self, admin_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/usuarios",
                json={
                    "nombre": "Ana Docente",
                    "email": "ana.api@fiuner.edu.ar",
                    "password": "claveSegura1",
                    "perfil": "docente",
                },
                headers=admin_headers,
            )

        assert response.status_code == 201
        body = response.json()
        assert body["email"] == "ana.api@fiuner.edu.ar"
        assert body["perfil"] == "docente"

    async def test_crear_usuario_email_duplicado_devuelve_409(self, admin_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            payload = {
                "nombre": "Ana",
                "email": "duplicado@fiuner.edu.ar",
                "password": "claveSegura1",
                "perfil": "docente",
            }
            await client.post("/usuarios", json=payload, headers=admin_headers)
            response = await client.post("/usuarios", json=payload, headers=admin_headers)

        assert response.status_code == 409
