"""Tests HTTP + WebSocket de `POST /sesiones-en-vivo/{sesion_id}/iniciar` (US-6.1.4).

Cubre uno a uno los escenarios de `tests/features/inc6/US-6.1.4-iniciar-sesion-en-vivo.feature`
contra la app real y la base de datos local.
"""

from __future__ import annotations

import asyncio
import uuid

from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from src.app import app
from src.shared.entities.tipo_perfil import TipoPerfil
from tests.integration.inc6._helpers import (
    correr,
    crear_estudiante,
    headers_de,
    iniciar_sesion,
    preparar_sesion,
    sembrar_evento_de_sesion,
)


def _cliente() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _docente() -> dict[str, str]:
    return headers_de(uuid.uuid4(), TipoPerfil.DOCENTE)


async def _eventos_de_sesion(session, sesion_id: str) -> list:
    resultado = await session.execute(
        text(
            "SELECT sequence_number, event_type, payload FROM events "
            "WHERE aggregate_type = 'ActividadEvaluativaEnVivo' AND aggregate_id = :id "
            "ORDER BY sequence_number"
        ),
        {"id": sesion_id},
    )
    return resultado.all()


class TestIniciarAPIIntegration:
    async def test_inicio_exitoso_con_un_estudiante_unido(self, session):
        sesion_id, comision_id = await preparar_sesion()
        _, headers = await crear_estudiante(comision_id)

        async with _cliente() as client:
            await client.post(f"/sesiones-en-vivo/{sesion_id}/unirse", headers=headers)
            response = await client.post(
                f"/sesiones-en-vivo/{sesion_id}/iniciar", headers=_docente()
            )

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == sesion_id
        assert body["estado"] == "EnCurso"
        assert body["pregunta_actual_indice"] == 0
        assert "preguntas" not in body

        eventos = await _eventos_de_sesion(session, sesion_id)
        assert [e.event_type for e in eventos] == ["SesionEnVivoCreada", "SesionEnVivoIniciada"]
        assert eventos[1].sequence_number == 2
        pregunta = eventos[1].payload["pregunta"]
        assert pregunta["enunciado"].startswith("Pregunta ")
        assert pregunta["tipo"] == "verdadero_falso"
        assert pregunta["pregunta_id"] == eventos[0].payload["preguntas"][0]["pregunta_id"]
        assert "opciones" not in pregunta

    async def test_inicio_sin_ningun_estudiante_unido(self):
        sesion_id, _ = await preparar_sesion()

        async with _cliente() as client:
            response = await client.post(
                f"/sesiones-en-vivo/{sesion_id}/iniciar", headers=_docente()
            )

        assert response.status_code == 200
        assert response.json()["estado"] == "EnCurso"

    async def test_rechazo_por_sesion_ya_iniciada(self, session):
        sesion_id, _ = await preparar_sesion()
        await iniciar_sesion(sesion_id)

        async with _cliente() as client:
            response = await client.post(
                f"/sesiones-en-vivo/{sesion_id}/iniciar", headers=_docente()
            )

        assert response.status_code == 422
        assert "iniciada" in response.json()["detail"]
        assert len(await _eventos_de_sesion(session, sesion_id)) == 2

    async def test_rechazo_por_sesion_finalizada(self):
        sesion_id, _ = await preparar_sesion()
        await iniciar_sesion(sesion_id)
        await sembrar_evento_de_sesion(sesion_id, "SesionEnVivoFinalizada", 3)

        async with _cliente() as client:
            response = await client.post(
                f"/sesiones-en-vivo/{sesion_id}/iniciar", headers=_docente()
            )

        assert response.status_code == 422

    async def test_sesion_inexistente(self):
        async with _cliente() as client:
            response = await client.post(
                f"/sesiones-en-vivo/{uuid.uuid4()}/iniciar", headers=_docente()
            )

        assert response.status_code == 404

    async def test_rechazo_por_rol_estudiante(self):
        sesion_id, comision_id = await preparar_sesion()
        _, headers = await crear_estudiante(comision_id)

        async with _cliente() as client:
            response = await client.post(f"/sesiones-en-vivo/{sesion_id}/iniciar", headers=headers)

        assert response.status_code == 403

    async def test_sin_token_se_rechaza(self):
        async with _cliente() as client:
            response = await client.post(f"/sesiones-en-vivo/{uuid.uuid4()}/iniciar")

        assert response.status_code in (401, 403)

    async def test_dos_inicios_simultaneos_dejan_ganar_a_uno_solo(self, session):
        sesion_id, _ = await preparar_sesion()

        async with _cliente() as client:
            respuestas = await asyncio.gather(
                client.post(f"/sesiones-en-vivo/{sesion_id}/iniciar", headers=_docente()),
                client.post(f"/sesiones-en-vivo/{sesion_id}/iniciar", headers=_docente()),
            )

        assert sorted(r.status_code for r in respuestas) == [200, 422]
        assert len(await _eventos_de_sesion(session, sesion_id)) == 2

    async def test_un_estudiante_puede_unirse_despues_de_iniciada(self):
        sesion_id, comision_id = await preparar_sesion()
        await iniciar_sesion(sesion_id)
        _, headers = await crear_estudiante(comision_id)

        async with _cliente() as client:
            response = await client.post(f"/sesiones-en-vivo/{sesion_id}/unirse", headers=headers)

        assert response.status_code == 200


class TestBroadcastATodosLosConectados:
    """Sincrónico: `TestClient` mantiene abiertos los WebSockets mientras el Docente inicia."""

    def test_docente_y_estudiante_reciben_el_enunciado_sin_opciones(self) -> None:
        sesion_id, comision_id = correr(preparar_sesion())
        docente = _docente()
        token_docente = docente["Authorization"].split()[1]
        _, headers_estudiante = correr(crear_estudiante(comision_id))
        token_estudiante = headers_estudiante["Authorization"].split()[1]

        with TestClient(app) as client:
            with (
                client.websocket_connect(
                    f"/sesiones-en-vivo/{sesion_id}/canal?token={token_docente}"
                ) as ws_docente,
                client.websocket_connect(
                    f"/sesiones-en-vivo/{sesion_id}/canal?token={token_estudiante}"
                ) as ws_estudiante,
            ):
                response = client.post(f"/sesiones-en-vivo/{sesion_id}/iniciar", headers=docente)
                assert response.status_code == 200

                recibidos = [ws_docente.receive_json(), ws_estudiante.receive_json()]

        for mensaje in recibidos:
            assert mensaje["tipo"] == "pregunta_presentada"
            assert mensaje["pregunta_actual_indice"] == 0
            assert mensaje["pregunta"]["enunciado"].startswith("Pregunta ")
            assert mensaje["pregunta"]["tipo"] == "verdadero_falso"
            assert "opciones" not in mensaje["pregunta"]
