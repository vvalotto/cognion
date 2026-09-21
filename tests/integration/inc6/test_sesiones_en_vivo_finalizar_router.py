"""Tests HTTP + WebSocket de `POST /sesiones-en-vivo/{sesion_id}/finalizar` (US-6.2.7).

Cubre los escenarios de `tests/features/inc6/US-6.2.7-finalizar-sesion-en-vivo.feature` contra
la app real y la base de datos local.
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
    cerrar_pregunta_actual,
    correr,
    crear_estudiante,
    headers_de,
    iniciar_sesion,
    mostrar_opciones,
    preparar_sesion,
)


def _cliente() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _docente() -> dict[str, str]:
    return headers_de(uuid.uuid4(), TipoPerfil.DOCENTE)


def _url(sesion_id: str, accion: str = "finalizar") -> str:
    return f"/sesiones-en-vivo/{sesion_id}/{accion}"


async def _eventos_de_sesion(session, sesion_id: str) -> list:
    resultado = await session.execute(
        text(
            "SELECT event_type, payload FROM events "
            "WHERE aggregate_type = 'ActividadEvaluativaEnVivo' AND aggregate_id = :id "
            "ORDER BY sequence_number"
        ),
        {"id": sesion_id},
    )
    return resultado.all()


async def _finalizar(sesion_id: str):
    async with _cliente() as client:
        return await client.post(_url(sesion_id), headers=_docente())


async def _sesion_cerrada() -> tuple[str, str]:
    """Sesión iniciada en la pregunta 1 de 5, con opciones mostradas y ya cerrada."""
    sesion_id, comision_id = await preparar_sesion(opcion_multiple=True)
    await iniciar_sesion(sesion_id)
    await mostrar_opciones(sesion_id)
    await cerrar_pregunta_actual(sesion_id)
    return sesion_id, comision_id


class TestFinalizarAPIIntegration:
    async def test_finalizacion_persiste_el_evento_y_devuelve_el_estado(self, session):
        sesion_id, _ = await _sesion_cerrada()

        response = await _finalizar(sesion_id)

        assert response.status_code == 200
        assert response.json()["estado"] == "Finalizada"
        eventos = await _eventos_de_sesion(session, sesion_id)
        assert eventos[-1].event_type == "SesionEnVivoFinalizada"
        assert "ranking" not in eventos[-1].payload

    async def test_finalizacion_anticipada_en_la_primera_de_cinco(self):
        sesion_id, _ = await _sesion_cerrada()

        response = await _finalizar(sesion_id)

        assert response.status_code == 200
        assert response.json()["pregunta_actual_indice"] == 0

    async def test_despues_de_finalizar_no_se_puede_unir_nadie(self):
        sesion_id, comision_id = await _sesion_cerrada()
        await _finalizar(sesion_id)
        _, headers = await crear_estudiante(comision_id)

        async with _cliente() as client:
            response = await client.post(_url(sesion_id, "unirse"), headers=headers)

        assert response.status_code == 422

    async def test_despues_de_finalizar_no_se_puede_iniciar(self):
        sesion_id, _ = await _sesion_cerrada()
        await _finalizar(sesion_id)

        async with _cliente() as client:
            response = await client.post(_url(sesion_id, "iniciar"), headers=_docente())

        assert response.status_code == 422

    async def test_rechazo_si_la_pregunta_no_fue_cerrada(self, session):
        sesion_id, _ = await preparar_sesion(opcion_multiple=True)
        await iniciar_sesion(sesion_id)
        await mostrar_opciones(sesion_id)

        response = await _finalizar(sesion_id)

        assert response.status_code == 422
        assert "cerrada" in response.json()["detail"]
        assert len(await _eventos_de_sesion(session, sesion_id)) == 3

    async def test_rechazo_si_la_sesion_esta_en_espera(self, session):
        sesion_id, _ = await preparar_sesion()

        response = await _finalizar(sesion_id)

        assert response.status_code == 422
        assert "no está en curso" in response.json()["detail"]
        assert len(await _eventos_de_sesion(session, sesion_id)) == 1

    async def test_rechazo_si_ya_estaba_finalizada_sin_otro_evento(self, session):
        sesion_id, _ = await _sesion_cerrada()
        await _finalizar(sesion_id)
        antes = len(await _eventos_de_sesion(session, sesion_id))

        response = await _finalizar(sesion_id)

        assert response.status_code == 422
        assert len(await _eventos_de_sesion(session, sesion_id)) == antes

    async def test_sesion_inexistente(self):
        response = await _finalizar(str(uuid.uuid4()))

        assert response.status_code == 404

    async def test_rechazo_por_rol_estudiante(self):
        sesion_id, comision_id = await _sesion_cerrada()
        _, headers = await crear_estudiante(comision_id)

        async with _cliente() as client:
            response = await client.post(_url(sesion_id), headers=headers)

        assert response.status_code == 403

    async def test_sin_token_se_rechaza(self):
        async with _cliente() as client:
            response = await client.post(_url(str(uuid.uuid4())))

        assert response.status_code in (401, 403)

    async def test_dos_finalizaciones_simultaneas_dejan_ganar_a_una_sola(self, session):
        sesion_id, _ = await _sesion_cerrada()

        async with _cliente() as client:
            respuestas = await asyncio.gather(
                client.post(_url(sesion_id), headers=_docente()),
                client.post(_url(sesion_id), headers=_docente()),
            )

        assert sorted(r.status_code for r in respuestas) == [200, 422]
        assert len(await _eventos_de_sesion(session, sesion_id)) == 5


class TestBroadcastDelRankingFinal:
    """Sincrónico: `TestClient` mantiene abiertos los WebSockets mientras el Docente finaliza."""

    def test_docente_y_estudiante_reciben_el_ranking_final(self) -> None:
        sesion_id, comision_id = correr(_sesion_cerrada())
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
                assert client.post(_url(sesion_id), headers=docente).status_code == 200
                recibidos = [ws_docente.receive_json(), ws_estudiante.receive_json()]

        assert recibidos[0] == recibidos[1]
        assert recibidos[0]["tipo"] == "sesion_finalizada"
        assert recibidos[0]["ranking"] == []
