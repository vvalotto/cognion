"""Tests de integración de los endpoints públicos de consulta para autoregistro (`US-ADJ-43`).

Gap de Fase 2: `GET /materias` (`US-2.1.9`) y `GET /materias/{id}/comisiones` (`US-4.2.2`)
exigen JWT de rol `docente`/`administrador` — un Estudiante autoregistrándose no tiene cuenta
todavía. Estos endpoints nuevos, bajo el mismo prefijo `/identidad/autoregistro`, no exigen
`Authorization` y exponen solo `id`/`nombre` (materias) e `id`/`horario` (comisiones).
"""

import uuid

from httpx import ASGITransport, AsyncClient

from src.app import app


async def _crear_materia(client, admin_headers) -> str:
    materia_resp = await client.post(
        "/materias", json={"nombre": f"Materia {uuid.uuid4()}"}, headers=admin_headers
    )
    return materia_resp.json()["id"]


async def _crear_comision(client, materia_id, admin_headers) -> dict:
    admin_resp = await client.post(
        "/usuarios",
        json={
            "nombre": "Admin",
            "email": f"admin.{uuid.uuid4()}@fiuner.edu.ar",
            "password": "claveSegura1#",
            "perfil": "administrador",
        },
        headers=admin_headers,
    )
    admin_id = admin_resp.json()["id"]

    comision_resp = await client.post(
        "/comisiones",
        json={"materia_id": materia_id, "horario": "lu 10-12", "administrador_id": admin_id},
        headers=admin_headers,
    )
    return comision_resp.json()


class TestListarMateriasAutoregistroAPIIntegration:
    async def test_lista_materias_sin_jwt(self, session, docente_headers, admin_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia(client, admin_headers)

            response = await client.get("/identidad/autoregistro/materias")

        assert response.status_code == 200
        materias = response.json()
        assert any(materia["id"] == materia_id for materia in materias)
        primera = next(materia for materia in materias if materia["id"] == materia_id)
        assert set(primera.keys()) == {"id", "nombre"}

    async def test_rechaza_authorization_no_es_necesario_devuelve_200_igual(
        self, session, docente_headers
    ):
        """Un JWT presente no rompe el endpoint público (no lo exige, pero lo tolera)."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/identidad/autoregistro/materias", headers=docente_headers)

        assert response.status_code == 200


class TestListarComisionesAutoregistroAPIIntegration:
    async def test_lista_comisiones_de_una_materia_sin_jwt(
        self, session, docente_headers, admin_headers
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia(client, admin_headers)
            comision = await _crear_comision(client, materia_id, admin_headers)

            response = await client.get(f"/identidad/autoregistro/materias/{materia_id}/comisiones")

        assert response.status_code == 200
        comisiones = response.json()
        assert len(comisiones) == 1
        assert comisiones[0]["id"] == comision["id"]
        assert comisiones[0]["horario"] == "lu 10-12"
        assert set(comisiones[0].keys()) == {"id", "horario"}

    async def test_materia_sin_comisiones_devuelve_lista_vacia(self, session, docente_headers, admin_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia(client, admin_headers)

            response = await client.get(f"/identidad/autoregistro/materias/{materia_id}/comisiones")

        assert response.status_code == 200
        assert response.json() == []

    async def test_materia_inexistente_devuelve_lista_vacia(self, session):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/identidad/autoregistro/materias/{uuid.uuid4()}/comisiones"
            )

        assert response.status_code == 200
        assert response.json() == []
