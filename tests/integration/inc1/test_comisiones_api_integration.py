from httpx import ASGITransport, AsyncClient

from src.app import app


class TestComisionesAPIIntegration:
    async def test_flujo_completo_crear_comision_y_asignar_docente(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            docente_resp = await client.post(
                "/usuarios",
                json={
                    "nombre": "Ana Docente",
                    "email": "docente.flujo@fiuner.edu.ar",
                    "password": "claveSegura1",
                    "perfil": "docente",
                },
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
            )
            admin_id = admin_resp.json()["id"]

            comision_resp = await client.post(
                "/comisiones",
                json={"materia": "IS", "horario": "lu 10-12", "administrador_id": admin_id},
            )
            comision_id = comision_resp.json()["id"]

            asignar_resp = await client.post(
                f"/comisiones/{comision_id}/docentes", json={"docente_id": docente_id}
            )

        assert comision_resp.status_code == 201
        assert asignar_resp.status_code == 200
        assert docente_id in asignar_resp.json()["docentes_asignados"]

    async def test_asignar_no_docente_devuelve_422(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            admin_resp = await client.post(
                "/usuarios",
                json={
                    "nombre": "Admin",
                    "email": "admin2.flujo@fiuner.edu.ar",
                    "password": "claveSegura1",
                    "perfil": "administrador",
                },
            )
            admin_id = admin_resp.json()["id"]

            comision_resp = await client.post(
                "/comisiones",
                json={"materia": "IS", "horario": "lu 10-12", "administrador_id": admin_id},
            )
            comision_id = comision_resp.json()["id"]

            response = await client.post(
                f"/comisiones/{comision_id}/docentes", json={"docente_id": admin_id}
            )

        assert response.status_code == 422
