import uuid

from httpx import ASGITransport, AsyncClient

from src.app import app


async def _crear_comision(client, admin_headers, docente_headers) -> str:
    materia_resp = await client.post(
        "/materias", json={"nombre": f"Materia {uuid.uuid4()}"}, headers=docente_headers
    )
    materia_id = materia_resp.json()["id"]

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
    return comision_resp.json()["id"]


class TestAutoregistroEstudianteAPIIntegration:
    async def test_autoregistro_exitoso_crea_estudiante_activo(
        self, session, admin_headers, docente_headers
    ):
        email = f"estudiante.nuevo.{uuid.uuid4()}@fiuner.edu.ar"

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            comision_id = await _crear_comision(client, admin_headers, docente_headers)

            response = await client.post(
                "/identidad/autoregistro/estudiante",
                json={
                    "nombre": "Vale Estudiante",
                    "email": email,
                    "password": "claveSegura1#",
                    "comision_id": comision_id,
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == email
        assert data["tipo_perfil"] == "estudiante"

    async def test_autoregistro_rechaza_email_ya_registrado(
        self, session, admin_headers, docente_headers
    ):
        email = f"estudiante.duplicado.{uuid.uuid4()}@fiuner.edu.ar"

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            comision_id = await _crear_comision(client, admin_headers, docente_headers)

            primera = await client.post(
                "/identidad/autoregistro/estudiante",
                json={
                    "nombre": "Vale",
                    "email": email,
                    "password": "claveSegura1#",
                    "comision_id": comision_id,
                },
            )
            assert primera.status_code == 201

            segunda = await client.post(
                "/identidad/autoregistro/estudiante",
                json={
                    "nombre": "Otra",
                    "email": email,
                    "password": "claveSegura2#",
                    "comision_id": comision_id,
                },
            )

        assert segunda.status_code == 409

    async def test_autoregistro_rechaza_comision_inexistente(self, session):
        email = f"estudiante.sincomision.{uuid.uuid4()}@fiuner.edu.ar"

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/identidad/autoregistro/estudiante",
                json={
                    "nombre": "Vale",
                    "email": email,
                    "password": "claveSegura1#",
                    "comision_id": str(uuid.uuid4()),
                },
            )

        assert response.status_code == 422

    async def test_autoregistro_rechaza_password_debil(
        self, session, admin_headers, docente_headers
    ):
        email = f"estudiante.debil.{uuid.uuid4()}@fiuner.edu.ar"

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            comision_id = await _crear_comision(client, admin_headers, docente_headers)

            response = await client.post(
                "/identidad/autoregistro/estudiante",
                json={
                    "nombre": "Vale",
                    "email": email,
                    "password": "abc123",
                    "comision_id": comision_id,
                },
            )

        assert response.status_code == 422

    async def test_estudiante_autoregistrado_puede_loguearse_de_inmediato(
        self, session, admin_headers, docente_headers
    ):
        email = f"estudiante.login.{uuid.uuid4()}@fiuner.edu.ar"

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            comision_id = await _crear_comision(client, admin_headers, docente_headers)

            crear = await client.post(
                "/identidad/autoregistro/estudiante",
                json={
                    "nombre": "Vale",
                    "email": email,
                    "password": "claveSegura1#",
                    "comision_id": comision_id,
                },
            )
            assert crear.status_code == 201

            login = await client.post(
                "/identidad/login", json={"email": email, "password": "claveSegura1#"}
            )

        assert login.status_code == 200
        assert login.json()["rol"] == "estudiante"
