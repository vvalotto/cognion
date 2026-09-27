"""Tests HTTP + WebSocket de `POST /sesiones-en-vivo/{sesion_id}/cancelar` (US-ADJ-58).

Cubre los escenarios backend de `tests/features/inc6-adj/US-ADJ-58-cancelar-finalizar-sesion.feature`
contra la app real y una base de datos PostgreSQL.
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
    unirse_a_sesion,
)


def _cliente() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _docente() -> dict[str, str]:
    return headers_de(uuid.uuid4(), TipoPerfil.DOCENTE)


def _url(sesion_id: str, accion: str = "cancelar") -> str:
    return f"/sesiones-en-vivo/{sesion_id}/{accion}"


async def _eventos_de_sesion(session, sesion_id: str) -> list[str]:
    resultado = await session.execute(
        text(
            "SELECT event_type FROM events "
            "WHERE aggregate_type = 'ActividadEvaluativaEnVivo' AND aggregate_id = :id "
            "ORDER BY sequence_number"
        ),
        {"id": sesion_id},
    )
    return [fila.event_type for fila in resultado.all()]


async def _cancelar(sesion_id: str):
    async with _cliente() as client:
        return await client.post(_url(sesion_id), headers=_docente())


class TestCancelarAPIIntegration:
    async def test_cancela_una_sesion_en_espera(self, session):
        sesion_id, _ = await preparar_sesion()

        response = await _cancelar(sesion_id)

        assert response.status_code == 200
        assert response.json()["estado"] == "Cancelada"
        assert await _eventos_de_sesion(session, sesion_id) == [
            "SesionEnVivoCreada",
            "SesionEnVivoCancelada",
        ]

    async def test_deja_de_figurar_en_el_listado_de_sesiones_activas(self):
        sesion_id, comision_id = await preparar_sesion()
        await _cancelar(sesion_id)

        async with _cliente() as client:
            activas = await client.get(
                "/sesiones-en-vivo",
                params={"comision_id": comision_id, "estado": ["EnEspera", "EnCurso"]},
                headers=_docente(),
            )
            canceladas = await client.get(
                "/sesiones-en-vivo",
                params={"comision_id": comision_id, "estado": ["Cancelada"]},
                headers=_docente(),
            )

        assert activas.status_code == 200
        assert activas.json() == []
        assert [s["id"] for s in canceladas.json()] == [sesion_id]

    async def test_una_sesion_iniciada_no_se_cancela(self, session):
        sesion_id, _ = await preparar_sesion()
        await iniciar_sesion(sesion_id)

        response = await _cancelar(sesion_id)

        assert response.status_code == 422
        assert "iniciada" in response.json()["detail"]
        assert (await _eventos_de_sesion(session, sesion_id))[-1] == "SesionEnVivoIniciada"

    async def test_cancelar_dos_veces_no_emite_otro_evento(self, session):
        sesion_id, _ = await preparar_sesion()
        await _cancelar(sesion_id)

        response = await _cancelar(sesion_id)

        assert response.status_code == 422
        assert "cancelada" in response.json()["detail"]
        assert len(await _eventos_de_sesion(session, sesion_id)) == 2

    async def test_nadie_se_une_a_una_sesion_cancelada(self):
        sesion_id, comision_id = await preparar_sesion()
        await _cancelar(sesion_id)
        _, headers = await crear_estudiante(comision_id)

        async with _cliente() as client:
            response = await client.post(_url(sesion_id, "unirse"), headers=headers)

        assert response.status_code == 422
        assert "cancelada" in response.json()["detail"]

    async def test_una_sesion_cancelada_no_se_inicia(self):
        sesion_id, comision_id = await preparar_sesion()
        _, headers = await crear_estudiante(comision_id)
        await unirse_a_sesion(sesion_id, headers)
        await _cancelar(sesion_id)

        async with _cliente() as client:
            response = await client.post(_url(sesion_id, "iniciar"), headers=_docente())

        assert response.status_code == 422
        assert "cancelada" in response.json()["detail"]

    async def test_sesion_inexistente(self):
        response = await _cancelar(str(uuid.uuid4()))

        assert response.status_code == 404

    async def test_rechazo_por_rol_estudiante(self):
        sesion_id, comision_id = await preparar_sesion()
        _, headers = await crear_estudiante(comision_id)

        async with _cliente() as client:
            response = await client.post(_url(sesion_id), headers=headers)

        assert response.status_code == 403

    async def test_cancelar_e_iniciar_a_la_vez_deja_ganar_a_uno_solo(self, session):
        sesion_id, comision_id = await preparar_sesion()
        _, headers = await crear_estudiante(comision_id)
        await unirse_a_sesion(sesion_id, headers)

        async with _cliente() as client:
            respuestas = await asyncio.gather(
                client.post(_url(sesion_id), headers=_docente()),
                client.post(_url(sesion_id, "iniciar"), headers=_docente()),
            )

        assert sorted(r.status_code for r in respuestas) == [200, 422]
        assert len(await _eventos_de_sesion(session, sesion_id)) == 2


class TestIniciarSinParticipantes:
    """INV-AEV-11 (`US-ADJ-58`): la API rechaza iniciar sin Estudiantes unidos."""

    async def test_sin_participantes_se_rechaza(self, session):
        sesion_id, _ = await preparar_sesion()

        async with _cliente() as client:
            response = await client.post(_url(sesion_id, "iniciar"), headers=_docente())

        assert response.status_code == 422
        assert "no tiene participantes" in response.json()["detail"]
        assert await _eventos_de_sesion(session, sesion_id) == ["SesionEnVivoCreada"]

    async def test_con_un_participante_se_inicia(self):
        sesion_id, comision_id = await preparar_sesion()
        _, headers = await crear_estudiante(comision_id)
        await unirse_a_sesion(sesion_id, headers)

        async with _cliente() as client:
            response = await client.post(_url(sesion_id, "iniciar"), headers=_docente())

        assert response.status_code == 200
        assert response.json()["estado"] == "EnCurso"


class TestBroadcastDeLaCancelacion:
    """Sincrónico: `TestClient` mantiene abiertos los WebSockets mientras el Docente cancela."""

    def test_los_estudiantes_en_la_sala_reciben_sesion_cancelada(self) -> None:
        sesion_id, comision_id = correr(preparar_sesion())
        docente = _docente()
        estudiantes = [correr(crear_estudiante(comision_id)) for _ in range(2)]
        for _, headers in estudiantes:
            correr(unirse_a_sesion(sesion_id, headers))
        tokens = [headers["Authorization"].split()[1] for _, headers in estudiantes]

        with TestClient(app) as client:
            with (
                client.websocket_connect(
                    f"/sesiones-en-vivo/{sesion_id}/canal?token={tokens[0]}"
                ) as ws_uno,
                client.websocket_connect(
                    f"/sesiones-en-vivo/{sesion_id}/canal?token={tokens[1]}"
                ) as ws_dos,
            ):
                assert client.post(_url(sesion_id), headers=docente).status_code == 200
                recibidos = [ws_uno.receive_json(), ws_dos.receive_json()]

        assert recibidos == [{"tipo": "sesion_cancelada"}, {"tipo": "sesion_cancelada"}]
