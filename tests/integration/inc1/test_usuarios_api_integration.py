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


class TestListarCuentasAPIIntegration:
    """US-2.2.2: listado de cuentas con filtros por rol/estado/búsqueda."""

    async def test_listado_sin_filtros_devuelve_todas_las_cuentas(self, admin_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/usuarios",
                json={
                    "nombre": "Listado Uno",
                    "email": "listado.uno@fiuner.edu.ar",
                    "password": "claveSegura1",
                    "perfil": "docente",
                },
                headers=admin_headers,
            )
            response = await client.get("/usuarios", headers=admin_headers)

        assert response.status_code == 200
        emails = [c["email"] for c in response.json()]
        assert "listado.uno@fiuner.edu.ar" in emails

    async def test_filtro_por_rol_y_busqueda_por_email_parcial(self, admin_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/usuarios",
                json={
                    "nombre": "Marisa Gonzalez",
                    "email": "mgonzalez.api@fiuner.edu.ar",
                    "password": "claveSegura1",
                    "perfil": "docente",
                },
                headers=admin_headers,
            )
            await client.post(
                "/usuarios",
                json={
                    "nombre": "Admin Distinto",
                    "email": "admin.distinto@fiuner.edu.ar",
                    "password": "claveSegura1",
                    "perfil": "administrador",
                },
                headers=admin_headers,
            )

            response = await client.get(
                "/usuarios",
                params={"rol": "docente", "busqueda": "mgonzalez"},
                headers=admin_headers,
            )

        assert response.status_code == 200
        cuentas = response.json()
        assert len(cuentas) == 1
        assert cuentas[0]["email"] == "mgonzalez.api@fiuner.edu.ar"
        assert cuentas[0]["perfil"] == "docente"
        assert cuentas[0]["bloqueada"] is False

    async def test_filtro_por_estado_activa(self, admin_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/usuarios",
                json={
                    "nombre": "Cuenta Activa",
                    "email": "activa.api@fiuner.edu.ar",
                    "password": "claveSegura1",
                    "perfil": "docente",
                },
                headers=admin_headers,
            )

            response = await client.get(
                "/usuarios", params={"estado": "activa"}, headers=admin_headers
            )

        assert response.status_code == 200
        emails = [c["email"] for c in response.json()]
        assert "activa.api@fiuner.edu.ar" in emails
        assert all(c["bloqueada"] is False for c in response.json())

    async def test_requiere_rol_administrador(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/usuarios")

        assert response.status_code == 401
