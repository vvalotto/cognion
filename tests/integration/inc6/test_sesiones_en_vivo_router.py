"""Tests HTTP de `POST /sesiones-en-vivo` (US-6.1.2).

Cubre uno a uno los escenarios de `tests/features/inc6/US-6.1.2-crear-sesion-en-vivo.feature`,
contra la app real y la base de datos local (mismo criterio que `tests/integration/inc3`).
"""

from __future__ import annotations

import uuid

from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from src.app import app
from src.identidad.entities.comision import Comision
from src.identidad.entities.usuario import Usuario
from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher
from src.identidad.interface_adapters.gateways.comision_repository import (
    SQLAlchemyComisionRepository,
)
from src.identidad.interface_adapters.gateways.usuario_repository import (
    SQLAlchemyUsuarioRepository,
)
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.security.jwt_pyjwt import PyJWTIssuer


def _headers(usuario_id: uuid.UUID, rol: TipoPerfil) -> dict[str, str]:
    return {"Authorization": f"Bearer {PyJWTIssuer().emitir(usuario_id, rol).token}"}


async def _crear_materia_con_preguntas(
    client: AsyncClient,
    admin_headers: dict,
    docente_headers: dict,
    cantidad: int,
    unidad: str = "Unidad 1",
    tema: str = "Tema",
) -> str:
    creada = await client.post(
        "/materias", json={"nombre": f"Materia {uuid.uuid4()}"}, headers=admin_headers
    )
    banco_id = creada.json()["banco_id"]
    for i in range(cantidad):
        await client.post(
            "/preguntas/verdadero-falso",
            json={
                "banco_id": banco_id,
                "texto": f"Pregunta {i}",
                "respuesta_correcta": True,
                "unidad_tematica": unidad,
                "tema": tema,
                "dificultad": "medio",
                "importancia": "alto",
            },
            headers=docente_headers,
        )
    return creada.json()["id"]


async def _crear_comision(session, materia_id: str) -> str:
    hasher = BcryptPasswordHasher()
    admin = Usuario.crear(
        "Admin", f"admin.{uuid.uuid4()}@fiuner.edu.ar", hasher.hash("x"), TipoPerfil.ADMINISTRADOR
    )
    await SQLAlchemyUsuarioRepository(session).guardar(admin)
    comision = Comision.crear(uuid.UUID(materia_id), "lu 10-12", admin.id)
    await SQLAlchemyComisionRepository(session).guardar(comision)
    return str(comision.id)


async def _contar_streams_de_sesiones(session) -> int:
    resultado = await session.execute(
        text("SELECT count(DISTINCT aggregate_id) FROM events WHERE aggregate_type = :t"),
        {"t": "ActividadEvaluativaEnVivo"},
    )
    return resultado.scalar_one()


class TestCrearSesionEnVivoAPIIntegration:
    async def test_creacion_exitosa(self, session, docente_headers, admin_headers):
        antes = await _contar_streams_de_sesiones(session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(
                client, admin_headers, docente_headers, 20
            )
            comision_id = await _crear_comision(session, materia_id)

            response = await client.post(
                "/sesiones-en-vivo",
                json={
                    "comision_id": comision_id,
                    "cantidad_preguntas": 10,
                    "tiempo_limite_por_pregunta_segundos": 30,
                },
                headers=docente_headers,
            )

        assert response.status_code == 201
        body = response.json()
        assert body["comision_id"] == comision_id
        assert body["materia_id"] == materia_id
        assert body["cantidad_preguntas"] == 10
        assert body["tiempo_limite_por_pregunta_segundos"] == 30
        assert body["estado"] == "EnEspera"
        assert "preguntas" not in body

        fila = (
            await session.execute(
                text(
                    "SELECT sequence_number, event_type, payload FROM events "
                    "WHERE aggregate_type = 'ActividadEvaluativaEnVivo' AND aggregate_id = :id"
                ),
                {"id": body["id"]},
            )
        ).one()
        assert fila.sequence_number == 1
        assert fila.event_type == "SesionEnVivoCreada"
        assert len(fila.payload["preguntas"]) == 10
        assert await _contar_streams_de_sesiones(session) == antes + 1

    async def test_filtra_por_unidad_y_tema(self, session, docente_headers, admin_headers):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(
                client, admin_headers, docente_headers, 6, unidad="U9", tema="T9"
            )
            comision_id = await _crear_comision(session, materia_id)

            response = await client.post(
                "/sesiones-en-vivo",
                json={
                    "comision_id": comision_id,
                    "cantidad_preguntas": 4,
                    "tiempo_limite_por_pregunta_segundos": 20,
                    "unidad_tematica": "U9",
                    "tema": "T9",
                },
                headers=docente_headers,
            )

        assert response.status_code == 201
        assert response.json()["unidad_tematica"] == "U9"
        assert response.json()["tema"] == "T9"

    async def test_preguntas_insuficientes(self, session, docente_headers, admin_headers):
        antes = await _contar_streams_de_sesiones(session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(
                client, admin_headers, docente_headers, 5
            )
            comision_id = await _crear_comision(session, materia_id)

            response = await client.post(
                "/sesiones-en-vivo",
                json={
                    "comision_id": comision_id,
                    "cantidad_preguntas": 10,
                    "tiempo_limite_por_pregunta_segundos": 30,
                },
                headers=docente_headers,
            )

        assert response.status_code == 422
        assert await _contar_streams_de_sesiones(session) == antes

    async def test_tiempo_limite_invalido(self, session, docente_headers, admin_headers):
        antes = await _contar_streams_de_sesiones(session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(
                client, admin_headers, docente_headers, 20
            )
            comision_id = await _crear_comision(session, materia_id)

            response = await client.post(
                "/sesiones-en-vivo",
                json={
                    "comision_id": comision_id,
                    "cantidad_preguntas": 10,
                    "tiempo_limite_por_pregunta_segundos": 0,
                },
                headers=docente_headers,
            )

        assert response.status_code == 422
        assert "tiempo límite" in response.json()["detail"]
        assert await _contar_streams_de_sesiones(session) == antes

    async def test_comision_inexistente(self, docente_headers):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/sesiones-en-vivo",
                json={
                    "comision_id": str(uuid.uuid4()),
                    "cantidad_preguntas": 10,
                    "tiempo_limite_por_pregunta_segundos": 30,
                },
                headers=docente_headers,
            )

        assert response.status_code == 404

    async def test_rechazo_por_rol_estudiante(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/sesiones-en-vivo",
                json={
                    "comision_id": str(uuid.uuid4()),
                    "cantidad_preguntas": 10,
                    "tiempo_limite_por_pregunta_segundos": 30,
                },
                headers=_headers(uuid.uuid4(), TipoPerfil.ESTUDIANTE),
            )

        assert response.status_code == 403

    async def test_sin_token_se_rechaza(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/sesiones-en-vivo",
                json={
                    "comision_id": str(uuid.uuid4()),
                    "cantidad_preguntas": 10,
                    "tiempo_limite_por_pregunta_segundos": 30,
                },
            )

        assert response.status_code in (401, 403)

    async def test_cantidad_preguntas_cero_se_rechaza_por_schema(self, docente_headers):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/sesiones-en-vivo",
                json={
                    "comision_id": str(uuid.uuid4()),
                    "cantidad_preguntas": 0,
                    "tiempo_limite_por_pregunta_segundos": 30,
                },
                headers=docente_headers,
            )

        assert response.status_code == 422
