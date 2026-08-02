import uuid

from httpx import ASGITransport, AsyncClient

from src.app import app


class TestMateriasAPIIntegration:
    """Escenarios de `tests/features/inc2/US-2.1.1-alta-materia-banco.feature` (RF-04, RF-06)."""

    async def test_docente_crea_materia_nueva(self, docente_headers):
        nombre = f"Ingeniería de Software {uuid.uuid4()}"
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/materias", json={"nombre": nombre}, headers=docente_headers
            )

        assert response.status_code == 201
        data = response.json()
        assert data["nombre"] == nombre
        assert "id" in data
        assert "banco_id" in data

    async def test_rechazo_por_nombre_duplicado(self, docente_headers):
        nombre = f"Ingeniería de Software {uuid.uuid4()}"
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            primera = await client.post(
                "/materias", json={"nombre": nombre}, headers=docente_headers
            )
            segunda = await client.post(
                "/materias", json={"nombre": nombre}, headers=docente_headers
            )

        assert primera.status_code == 201
        assert segunda.status_code == 409

    async def test_rechazo_por_nombre_vacio(self, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/materias", json={"nombre": ""}, headers=docente_headers)

        assert response.status_code == 422

    async def test_rechazo_sin_autenticacion(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/materias", json={"nombre": "Sin sesión"})

        assert response.status_code == 401

    async def test_rechazo_con_rol_insuficiente(self, admin_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/materias", json={"nombre": "Rol insuficiente"}, headers=admin_headers
            )

        assert response.status_code == 403
