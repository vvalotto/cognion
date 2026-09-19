"""Tests HTTP + WebSocket de `POST /sesiones-en-vivo/{sesion_id}/unirse` (US-6.1.3).

Cubre uno a uno los escenarios de `tests/features/inc6/US-6.1.3-unirse-sesion-en-vivo.feature`
contra la app real y la base de datos local. Los estados `EnCurso`/`Finalizada` se siembran
directo en el event store (ver `_helpers.sembrar_evento_de_sesion`).
"""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from src.actividad_evaluativa.frameworks.adapters.participantes_sesion_query_repository import (
    SQLAlchemyParticipantesSesionQueryRepository,
)
from src.app import app
from src.shared.entities.tipo_perfil import TipoPerfil
from tests.integration.inc6._helpers import (
    correr,
    crear_estudiante,
    headers_de,
    preparar_sesion,
    sembrar_evento_de_sesion,
)


def _cliente() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _contar_participaciones(session, sesion_id: str) -> int:
    resultado = await session.execute(
        text(
            "SELECT count(*) FROM events WHERE aggregate_type = 'ParticipacionEnVivo' "
            "AND payload->>'sesion_id' = :sid"
        ),
        {"sid": sesion_id},
    )
    return resultado.scalar_one()


class TestUnirseAPIIntegration:
    async def test_union_mientras_la_sesion_esta_en_espera(self, session):
        sesion_id, comision_id = await preparar_sesion()
        estudiante_id, headers = await crear_estudiante(comision_id)

        async with _cliente() as client:
            response = await client.post(f"/sesiones-en-vivo/{sesion_id}/unirse", headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert body["sesion_id"] == sesion_id
        assert body["estudiante_id"] == estudiante_id
        assert await _contar_participaciones(session, sesion_id) == 1
        participantes = await SQLAlchemyParticipantesSesionQueryRepository(session).listar(
            uuid.UUID(sesion_id)
        )
        assert [str(p.estudiante_id) for p in participantes] == [estudiante_id]

    async def test_union_tardia_con_la_sesion_en_curso(self, session):
        sesion_id, comision_id = await preparar_sesion()
        await sembrar_evento_de_sesion(sesion_id, "SesionEnVivoIniciada", 2)
        _, headers = await crear_estudiante(comision_id)

        async with _cliente() as client:
            response = await client.post(f"/sesiones-en-vivo/{sesion_id}/unirse", headers=headers)

        assert response.status_code == 200
        assert await _contar_participaciones(session, sesion_id) == 1

    async def test_union_idempotente_no_crea_una_segunda_participacion(self, session):
        sesion_id, comision_id = await preparar_sesion()
        _, headers = await crear_estudiante(comision_id)

        async with _cliente() as client:
            primera = await client.post(f"/sesiones-en-vivo/{sesion_id}/unirse", headers=headers)
            segunda = await client.post(f"/sesiones-en-vivo/{sesion_id}/unirse", headers=headers)

        assert primera.status_code == 200
        assert segunda.status_code == 200
        assert segunda.json() == primera.json()
        assert await _contar_participaciones(session, sesion_id) == 1

    async def test_rechazo_por_sesion_finalizada(self, session):
        sesion_id, comision_id = await preparar_sesion()
        await sembrar_evento_de_sesion(sesion_id, "SesionEnVivoIniciada", 2)
        await sembrar_evento_de_sesion(sesion_id, "SesionEnVivoFinalizada", 3)
        _, headers = await crear_estudiante(comision_id)

        async with _cliente() as client:
            response = await client.post(f"/sesiones-en-vivo/{sesion_id}/unirse", headers=headers)

        assert response.status_code == 422
        assert "finalizada" in response.json()["detail"]
        assert await _contar_participaciones(session, sesion_id) == 0

    async def test_sesion_inexistente(self):
        _, comision_id = await preparar_sesion()
        _, headers = await crear_estudiante(comision_id)

        async with _cliente() as client:
            response = await client.post(
                f"/sesiones-en-vivo/{uuid.uuid4()}/unirse", headers=headers
            )

        assert response.status_code == 404

    async def test_estudiante_que_no_existe_en_identidad(self):
        sesion_id, _ = await preparar_sesion()

        async with _cliente() as client:
            response = await client.post(
                f"/sesiones-en-vivo/{sesion_id}/unirse",
                headers=headers_de(uuid.uuid4(), TipoPerfil.ESTUDIANTE),
            )

        assert response.status_code == 404

    async def test_rechazo_por_rol_docente(self):
        sesion_id, _ = await preparar_sesion()

        async with _cliente() as client:
            response = await client.post(
                f"/sesiones-en-vivo/{sesion_id}/unirse",
                headers=headers_de(uuid.uuid4(), TipoPerfil.DOCENTE),
            )

        assert response.status_code == 403

    async def test_sin_token_se_rechaza(self):
        async with _cliente() as client:
            response = await client.post(f"/sesiones-en-vivo/{uuid.uuid4()}/unirse")

        assert response.status_code in (401, 403)


class TestParticipantesSesionQueryRepository:
    async def test_lista_en_orden_de_union_y_aisla_por_sesion(self, session):
        sesion_a, comision_a = await preparar_sesion()
        sesion_b, comision_b = await preparar_sesion()
        primero, headers_1 = await crear_estudiante(comision_a)
        segundo, headers_2 = await crear_estudiante(comision_a)
        otro, headers_otro = await crear_estudiante(comision_b)

        async with _cliente() as client:
            await client.post(f"/sesiones-en-vivo/{sesion_a}/unirse", headers=headers_1)
            await client.post(f"/sesiones-en-vivo/{sesion_a}/unirse", headers=headers_2)
            await client.post(f"/sesiones-en-vivo/{sesion_b}/unirse", headers=headers_otro)

        repo = SQLAlchemyParticipantesSesionQueryRepository(session)
        en_a = await repo.listar(uuid.UUID(sesion_a))
        en_b = await repo.listar(uuid.UUID(sesion_b))

        assert [str(p.estudiante_id) for p in en_a] == [primero, segundo]
        assert [str(p.estudiante_id) for p in en_b] == [otro]

    async def test_sesion_sin_participantes_devuelve_lista_vacia(self, session):
        sesion_id, _ = await preparar_sesion()

        repo = SQLAlchemyParticipantesSesionQueryRepository(session)

        assert await repo.listar(uuid.UUID(sesion_id)) == []


class TestBroadcastAlDocente:
    """Sincrónico: `TestClient` mantiene abierto el WebSocket mientras otro request une al alumno."""

    def test_el_docente_conectado_recibe_la_lista_actualizada(self) -> None:
        sesion_id, comision_id = correr(preparar_sesion())
        _, headers = correr(crear_estudiante(comision_id))
        token = headers_de(uuid.uuid4(), TipoPerfil.DOCENTE)["Authorization"].split()[1]

        with TestClient(app) as client:
            with client.websocket_connect(
                f"/sesiones-en-vivo/{sesion_id}/canal?token={token}"
            ) as ws:
                response = client.post(f"/sesiones-en-vivo/{sesion_id}/unirse", headers=headers)
                assert response.status_code == 200

                mensaje = ws.receive_json()

        assert mensaje["tipo"] == "participantes_actualizados"
        assert mensaje["cantidad"] == 1
        assert mensaje["participantes"][0]["estudiante_id"] == response.json()["estudiante_id"]
