"""Tests HTTP + WebSocket de `POST /sesiones-en-vivo/{sesion_id}/mostrar-opciones` (US-6.2.2).

Cubre uno a uno los escenarios de `tests/features/inc6/US-6.2.2-mostrar-opciones-en-vivo.feature`
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


def _url(sesion_id: str) -> str:
    return f"/sesiones-en-vivo/{sesion_id}/mostrar-opciones"


class TestMostrarOpcionesAPIIntegration:
    async def test_opcion_multiple_registra_el_evento_sin_la_correcta(self, session):
        sesion_id, _ = await preparar_sesion(opcion_multiple=True)
        await iniciar_sesion(sesion_id)

        async with _cliente() as client:
            response = await client.post(_url(sesion_id), headers=_docente())

        assert response.status_code == 200
        assert response.json()["estado"] == "EnCurso"
        eventos = await _eventos_de_sesion(session, sesion_id)
        assert [e.event_type for e in eventos] == [
            "SesionEnVivoCreada",
            "SesionEnVivoIniciada",
            "OpcionesEnVivoMostradas",
        ]
        payload = eventos[2].payload
        assert payload["opciones"] == ["A", "B", "C", "D"]
        assert payload["pregunta_actual_indice"] == 0
        assert payload["pregunta_id"] == eventos[0].payload["preguntas"][0]["pregunta_id"]
        assert "ocurrido_en" in payload
        assert "es_correcta" not in str(payload)

    async def test_verdadero_falso_persiste_opciones_nulas(self, session):
        sesion_id, _ = await preparar_sesion()
        await iniciar_sesion(sesion_id)

        async with _cliente() as client:
            response = await client.post(_url(sesion_id), headers=_docente())

        assert response.status_code == 200
        eventos = await _eventos_de_sesion(session, sesion_id)
        assert eventos[2].payload["opciones"] is None

    async def test_rechazo_si_las_opciones_ya_estaban_mostradas(self, session):
        sesion_id, _ = await preparar_sesion()
        await iniciar_sesion(sesion_id)
        async with _cliente() as client:
            await client.post(_url(sesion_id), headers=_docente())
            response = await client.post(_url(sesion_id), headers=_docente())

        assert response.status_code == 422
        assert "ya se mostraron" in response.json()["detail"]
        assert len(await _eventos_de_sesion(session, sesion_id)) == 3

    async def test_rechazo_si_la_sesion_esta_en_espera(self, session):
        sesion_id, _ = await preparar_sesion()

        async with _cliente() as client:
            response = await client.post(_url(sesion_id), headers=_docente())

        assert response.status_code == 422
        assert "no está en curso" in response.json()["detail"]
        assert len(await _eventos_de_sesion(session, sesion_id)) == 1

    async def test_rechazo_si_la_sesion_esta_finalizada(self):
        sesion_id, _ = await preparar_sesion()
        await iniciar_sesion(sesion_id)
        await sembrar_evento_de_sesion(sesion_id, "SesionEnVivoFinalizada", 3)

        async with _cliente() as client:
            response = await client.post(_url(sesion_id), headers=_docente())

        assert response.status_code == 422

    async def test_sesion_inexistente(self):
        async with _cliente() as client:
            response = await client.post(_url(str(uuid.uuid4())), headers=_docente())

        assert response.status_code == 404

    async def test_rechazo_por_rol_estudiante(self):
        sesion_id, comision_id = await preparar_sesion()
        await iniciar_sesion(sesion_id)
        _, headers = await crear_estudiante(comision_id)

        async with _cliente() as client:
            response = await client.post(_url(sesion_id), headers=headers)

        assert response.status_code == 403

    async def test_sin_token_se_rechaza(self):
        async with _cliente() as client:
            response = await client.post(_url(str(uuid.uuid4())))

        assert response.status_code in (401, 403)

    async def test_dos_pedidos_simultaneos_dejan_ganar_a_uno_solo(self, session):
        sesion_id, _ = await preparar_sesion()
        await iniciar_sesion(sesion_id)

        async with _cliente() as client:
            respuestas = await asyncio.gather(
                client.post(_url(sesion_id), headers=_docente()),
                client.post(_url(sesion_id), headers=_docente()),
            )

        assert sorted(r.status_code for r in respuestas) == [200, 422]
        assert len(await _eventos_de_sesion(session, sesion_id)) == 3


class TestBroadcastATodosLosConectados:
    """Sincrónico: `TestClient` mantiene abiertos los WebSockets mientras el Docente muestra."""

    def test_docente_y_estudiante_reciben_las_opciones_sin_la_correcta(self) -> None:
        sesion_id, comision_id = correr(preparar_sesion(opcion_multiple=True))
        correr(iniciar_sesion(sesion_id))
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
                response = client.post(_url(sesion_id), headers=docente)
                assert response.status_code == 200

                recibidos = [ws_docente.receive_json(), ws_estudiante.receive_json()]

        for mensaje in recibidos:
            assert mensaje == {
                "tipo": "opciones_mostradas",
                "pregunta_actual_indice": 0,
                "opciones": ["A", "B", "C", "D"],
                "tiempo_limite_por_pregunta_segundos": 30,
                "cantidad_respuestas": 0,
            }

    def test_verdadero_falso_publica_opciones_nulas(self) -> None:
        sesion_id, _ = correr(preparar_sesion())
        correr(iniciar_sesion(sesion_id))
        docente = _docente()
        token_docente = docente["Authorization"].split()[1]

        with TestClient(app) as client:
            with client.websocket_connect(
                f"/sesiones-en-vivo/{sesion_id}/canal?token={token_docente}"
            ) as ws_docente:
                assert client.post(_url(sesion_id), headers=docente).status_code == 200
                mensaje = ws_docente.receive_json()

        assert mensaje["tipo"] == "opciones_mostradas"
        assert mensaje["opciones"] is None
