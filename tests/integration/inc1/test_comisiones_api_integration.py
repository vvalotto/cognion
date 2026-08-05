import uuid

from httpx import ASGITransport, AsyncClient

from src.app import app


async def _crear_materia(client, docente_headers, nombre: str) -> str:
    response = await client.post(
        "/materias",
        json={"nombre": nombre},
        headers=docente_headers,
    )
    return response.json()["id"]


class TestComisionesAPIIntegration:
    async def test_flujo_completo_crear_comision_y_asignar_docente(
        self, admin_headers, docente_headers
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia(client, docente_headers, f"IS {uuid.uuid4()}")

            docente_resp = await client.post(
                "/usuarios",
                json={
                    "nombre": "Ana Docente",
                    "email": "docente.flujo@fiuner.edu.ar",
                    "password": "claveSegura1",
                    "perfil": "docente",
                },
                headers=admin_headers,
            )
            docente_id = docente_resp.json()["id"]

            admin_resp = await client.post(
                "/usuarios",
                json={
                    "nombre": "Admin",
                    "email": "admin.flujo@fiuner.edu.ar",
                    "password": "claveSegura1",
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
            comision_id = comision_resp.json()["id"]

            asignar_resp = await client.post(
                f"/comisiones/{comision_id}/docentes",
                json={"docente_id": docente_id},
                headers=admin_headers,
            )

        assert comision_resp.status_code == 201
        assert comision_resp.json()["materia_id"] == materia_id
        assert asignar_resp.status_code == 200
        assert docente_id in asignar_resp.json()["docentes_asignados"]

    async def test_crear_comision_con_materia_inexistente_devuelve_422(
        self, admin_headers, docente_headers
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            admin_resp = await client.post(
                "/usuarios",
                json={
                    "nombre": "Admin",
                    "email": "admin.sinmateria@fiuner.edu.ar",
                    "password": "claveSegura1",
                    "perfil": "administrador",
                },
                headers=admin_headers,
            )
            admin_id = admin_resp.json()["id"]

            response = await client.post(
                "/comisiones",
                json={
                    "materia_id": str(uuid.uuid4()),
                    "horario": "lu 10-12",
                    "administrador_id": admin_id,
                },
                headers=admin_headers,
            )

        assert response.status_code == 422

    async def test_asignar_no_docente_devuelve_422(self, admin_headers, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia(client, docente_headers, f"IS {uuid.uuid4()}")

            admin_resp = await client.post(
                "/usuarios",
                json={
                    "nombre": "Admin",
                    "email": "admin2.flujo@fiuner.edu.ar",
                    "password": "claveSegura1",
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
            comision_id = comision_resp.json()["id"]

            response = await client.post(
                f"/comisiones/{comision_id}/docentes",
                json={"docente_id": admin_id},
                headers=admin_headers,
            )

        assert response.status_code == 422
