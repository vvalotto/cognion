import uuid
from datetime import UTC, datetime, timedelta

from httpx import ASGITransport, AsyncClient

from src.app import app


async def _crear_materia_con_preguntas(client: AsyncClient, headers: dict, cantidad: int) -> str:
    nombre = f"Ingeniería de Software {uuid.uuid4()}"
    creada = await client.post("/materias", json={"nombre": nombre}, headers=headers)
    banco_id = creada.json()["banco_id"]

    for i in range(cantidad):
        await client.post(
            "/preguntas/verdadero-falso",
            json={
                "banco_id": banco_id,
                "texto": f"Pregunta {i}",
                "respuesta_correcta": True,
                "unidad_tematica": "Unidad 1",
                "tema": "Tema",
                "dificultad": "medio",
                "importancia": "alto",
            },
            headers=headers,
        )

    return creada.json()["id"]


def _periodo() -> tuple[str, str]:
    apertura = datetime.now(UTC)
    cierre = apertura + timedelta(days=7)
    return apertura.isoformat(), cierre.isoformat()


class TestCrearActividadAPIIntegration:
    """Escenarios de `tests/features/inc3/US-3.1.2-crear-actividad-periodo-abierto.feature`."""

    async def test_docente_crea_actividad_valida(self, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(client, docente_headers, 20)
            apertura, cierre = _periodo()

            response = await client.post(
                "/actividades",
                json={
                    "materia_id": materia_id,
                    "fecha_apertura": apertura,
                    "fecha_cierre": cierre,
                    "cantidad_preguntas": 10,
                    "cantidad_intentos_permitidos": 1,
                },
                headers=docente_headers,
            )

        assert response.status_code == 201
        data = response.json()
        assert data["materia_id"] == materia_id
        assert data["cantidad_preguntas"] == 10
        assert data["cantidad_intentos_permitidos"] == 1
        assert data["cerrada_manualmente"] is False
        assert "id" in data

    async def test_rechazo_por_preguntas_insuficientes(self, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(client, docente_headers, 5)
            apertura, cierre = _periodo()

            response = await client.post(
                "/actividades",
                json={
                    "materia_id": materia_id,
                    "fecha_apertura": apertura,
                    "fecha_cierre": cierre,
                    "cantidad_preguntas": 10,
                    "cantidad_intentos_permitidos": 1,
                },
                headers=docente_headers,
            )

        assert response.status_code == 422

    async def test_rechazo_por_periodo_invalido(self, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(client, docente_headers, 20)
            apertura, cierre = _periodo()

            response = await client.post(
                "/actividades",
                json={
                    "materia_id": materia_id,
                    "fecha_apertura": cierre,
                    "fecha_cierre": apertura,
                    "cantidad_preguntas": 10,
                    "cantidad_intentos_permitidos": 1,
                },
                headers=docente_headers,
            )

        assert response.status_code == 422

    async def test_rechazo_por_cantidad_intentos_invalida(self, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(client, docente_headers, 20)
            apertura, cierre = _periodo()

            response = await client.post(
                "/actividades",
                json={
                    "materia_id": materia_id,
                    "fecha_apertura": apertura,
                    "fecha_cierre": cierre,
                    "cantidad_preguntas": 10,
                    "cantidad_intentos_permitidos": 0,
                },
                headers=docente_headers,
            )

        assert response.status_code == 422

    async def test_rechazo_por_materia_inexistente(self, docente_headers):
        transport = ASGITransport(app=app)
        apertura, cierre = _periodo()
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/actividades",
                json={
                    "materia_id": str(uuid.uuid4()),
                    "fecha_apertura": apertura,
                    "fecha_cierre": cierre,
                    "cantidad_preguntas": 10,
                    "cantidad_intentos_permitidos": 1,
                },
                headers=docente_headers,
            )

        assert response.status_code == 404

    async def test_rechazo_sin_autenticacion(self):
        transport = ASGITransport(app=app)
        apertura, cierre = _periodo()
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/actividades",
                json={
                    "materia_id": str(uuid.uuid4()),
                    "fecha_apertura": apertura,
                    "fecha_cierre": cierre,
                    "cantidad_preguntas": 10,
                    "cantidad_intentos_permitidos": 1,
                },
            )

        assert response.status_code == 401

    async def test_rechazo_con_rol_insuficiente(self, admin_headers):
        transport = ASGITransport(app=app)
        apertura, cierre = _periodo()
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/actividades",
                json={
                    "materia_id": str(uuid.uuid4()),
                    "fecha_apertura": apertura,
                    "fecha_cierre": cierre,
                    "cantidad_preguntas": 10,
                    "cantidad_intentos_permitidos": 1,
                },
                headers=admin_headers,
            )

        assert response.status_code == 403
