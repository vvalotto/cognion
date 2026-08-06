import uuid

from httpx import ASGITransport, AsyncClient

from src.app import app
from src.banco_preguntas.entities.banco import Banco
from src.banco_preguntas.entities.materia import Materia
from src.banco_preguntas.interface_adapters.gateways.banco_repository import (
    SQLAlchemyBancoRepository,
)
from src.banco_preguntas.interface_adapters.gateways.materia_repository import (
    SQLAlchemyMateriaRepository,
)


async def _banco_persistido(session) -> Banco:
    materia_repo = SQLAlchemyMateriaRepository(session)
    banco_repo = SQLAlchemyBancoRepository(session)
    materia = Materia.crear(f"Ingeniería de Software {uuid.uuid4()}")
    await materia_repo.guardar(materia)
    banco = Banco.crear(materia.id)
    await banco_repo.guardar(banco)
    return banco


def _body_valido(banco_id: uuid.UUID) -> dict:
    return {
        "banco_id": str(banco_id),
        "texto": "¿Cuál es la capital de Entre Ríos?",
        "opciones": [
            {"texto": "Paraná", "es_correcta": True},
            {"texto": "Concordia", "es_correcta": False},
            {"texto": "Gualeguaychú", "es_correcta": False},
        ],
        "unidad_tematica": "Unidad 1",
        "tema": "Arquitectura",
        "dificultad": "medio",
        "importancia": "alto",
    }


class TestPreguntasAPIIntegration:
    """Escenarios de `tests/features/inc2/US-2.1.3-cargar-pregunta-opcion-multiple.feature`."""

    async def test_docente_carga_pregunta_exitosa(self, session, docente_headers):
        banco = await _banco_persistido(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/preguntas/opcion-multiple",
                json=_body_valido(banco.id),
                headers=docente_headers,
            )

        assert response.status_code == 201
        data = response.json()
        assert data["banco_id"] == str(banco.id)
        assert data["activa"] is True
        assert len(data["opciones"]) == 3

    async def test_rechazo_por_ninguna_opcion_correcta(self, session, docente_headers):
        banco = await _banco_persistido(session)
        body = _body_valido(banco.id)
        body["opciones"] = [
            {"texto": "Paraná", "es_correcta": False},
            {"texto": "Concordia", "es_correcta": False},
        ]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/preguntas/opcion-multiple", json=body, headers=docente_headers
            )

        assert response.status_code == 422

    async def test_rechazo_por_mas_de_una_opcion_correcta(self, session, docente_headers):
        banco = await _banco_persistido(session)
        body = _body_valido(banco.id)
        body["opciones"] = [
            {"texto": "Paraná", "es_correcta": True},
            {"texto": "Concordia", "es_correcta": True},
        ]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/preguntas/opcion-multiple", json=body, headers=docente_headers
            )

        assert response.status_code == 422

    async def test_rechazo_por_menos_de_dos_opciones(self, session, docente_headers):
        banco = await _banco_persistido(session)
        body = _body_valido(banco.id)
        body["opciones"] = [{"texto": "Paraná", "es_correcta": True}]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/preguntas/opcion-multiple", json=body, headers=docente_headers
            )

        assert response.status_code == 422

    async def test_rechazo_por_banco_inexistente(self, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/preguntas/opcion-multiple",
                json=_body_valido(uuid.uuid4()),
                headers=docente_headers,
            )

        assert response.status_code == 404

    async def test_rechazo_sin_autenticacion(self, session):
        banco = await _banco_persistido(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/preguntas/opcion-multiple", json=_body_valido(banco.id)
            )

        assert response.status_code == 401

    async def test_rechazo_con_rol_insuficiente(self, session, admin_headers):
        banco = await _banco_persistido(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/preguntas/opcion-multiple",
                json=_body_valido(banco.id),
                headers=admin_headers,
            )

        assert response.status_code == 403
