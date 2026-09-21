"""Tests HTTP + WebSocket de `POST /sesiones-en-vivo/{sesion_id}/avanzar` (US-6.2.6).

Cubre los escenarios de `tests/features/inc6/US-6.2.6-avanzar-siguiente-pregunta.feature` contra
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
    correr,
    crear_estudiante,
    headers_de,
    iniciar_sesion,
    mostrar_opciones,
    preparar_sesion,
    sembrar_evento_de_sesion,
)


def _cliente() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _docente() -> dict[str, str]:
    return headers_de(uuid.uuid4(), TipoPerfil.DOCENTE)


def _url(sesion_id: str, accion: str = "avanzar") -> str:
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


async def _cerrar(sesion_id: str) -> None:
    async with _cliente() as client:
        respuesta = await client.post(_url(sesion_id, "cerrar-pregunta"), headers=_docente())
    assert respuesta.status_code == 200, respuesta.text


async def _avanzar(sesion_id: str):
    async with _cliente() as client:
        return await client.post(_url(sesion_id), headers=_docente())


async def _sesion_cerrada() -> tuple[str, str]:
    """Sesión iniciada en la pregunta 1 de 5, con opciones mostradas y ya cerrada."""
    sesion_id, comision_id = await preparar_sesion(opcion_multiple=True)
    await iniciar_sesion(sesion_id)
    await mostrar_opciones(sesion_id)
    await _cerrar(sesion_id)
    return sesion_id, comision_id


async def _llegar_a_la_ultima_cerrada(sesion_id: str) -> None:
    """Avanza 4 veces (mostrar → cerrar → avanzar) hasta la pregunta 5, y la deja cerrada."""
    for _ in range(4):
        assert (await _avanzar(sesion_id)).status_code == 200
        await mostrar_opciones(sesion_id)
        await _cerrar(sesion_id)


class TestAvanzarAPIIntegration:
    async def test_avance_exitoso_persiste_el_evento_y_devuelve_el_estado(self, session):
        sesion_id, _ = await _sesion_cerrada()

        response = await _avanzar(sesion_id)

        assert response.status_code == 200
        cuerpo = response.json()
        assert cuerpo["estado"] == "EnCurso"
        assert cuerpo["pregunta_actual_indice"] == 1
        eventos = await _eventos_de_sesion(session, sesion_id)
        assert eventos[-1].event_type == "SiguientePreguntaPresentada"
        assert eventos[-1].payload["pregunta_actual_indice"] == 1
        assert set(eventos[-1].payload["pregunta"]) == {"pregunta_id", "enunciado", "tipo"}

    async def test_tras_avanzar_se_puede_mostrar_opciones_de_la_nueva_pregunta(self):
        sesion_id, _ = await _sesion_cerrada()
        await _avanzar(sesion_id)

        async with _cliente() as client:
            response = await client.post(_url(sesion_id, "mostrar-opciones"), headers=_docente())

        assert response.status_code == 200

    async def test_avance_hasta_la_penultima_deja_en_la_pregunta_5(self):
        sesion_id, _ = await _sesion_cerrada()
        for _ in range(3):
            assert (await _avanzar(sesion_id)).status_code == 200
            await mostrar_opciones(sesion_id)
            await _cerrar(sesion_id)

        response = await _avanzar(sesion_id)

        assert response.status_code == 200
        assert response.json()["pregunta_actual_indice"] == 4

    async def test_rechazo_si_la_pregunta_no_fue_cerrada(self, session):
        sesion_id, _ = await preparar_sesion(opcion_multiple=True)
        await iniciar_sesion(sesion_id)
        await mostrar_opciones(sesion_id)

        response = await _avanzar(sesion_id)

        assert response.status_code == 422
        assert "cerrada" in response.json()["detail"]
        assert len(await _eventos_de_sesion(session, sesion_id)) == 3

    async def test_rechazo_en_la_ultima_pregunta(self, session):
        sesion_id, _ = await _sesion_cerrada()
        await _llegar_a_la_ultima_cerrada(sesion_id)
        antes = len(await _eventos_de_sesion(session, sesion_id))

        response = await _avanzar(sesion_id)

        assert response.status_code == 422
        assert "más preguntas" in response.json()["detail"]
        assert len(await _eventos_de_sesion(session, sesion_id)) == antes

    async def test_rechazo_si_la_sesion_esta_en_espera(self):
        sesion_id, _ = await preparar_sesion()

        response = await _avanzar(sesion_id)

        assert response.status_code == 422
        assert "no está en curso" in response.json()["detail"]

    async def test_rechazo_si_la_sesion_esta_finalizada(self):
        sesion_id, _ = await _sesion_cerrada()
        await sembrar_evento_de_sesion(sesion_id, "SesionEnVivoFinalizada", 5)

        response = await _avanzar(sesion_id)

        assert response.status_code == 422

    async def test_sesion_inexistente(self):
        response = await _avanzar(str(uuid.uuid4()))

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

    async def test_dos_avances_simultaneos_dejan_ganar_a_uno_solo(self, session):
        sesion_id, _ = await _sesion_cerrada()

        async with _cliente() as client:
            respuestas = await asyncio.gather(
                client.post(_url(sesion_id), headers=_docente()),
                client.post(_url(sesion_id), headers=_docente()),
            )

        assert sorted(r.status_code for r in respuestas) == [200, 422]
        assert len(await _eventos_de_sesion(session, sesion_id)) == 5


class TestBroadcastATodosLosConectados:
    """Sincrónico: `TestClient` mantiene abiertos los WebSockets mientras el Docente avanza."""

    def test_docente_y_estudiante_reciben_el_enunciado_sin_opciones(self) -> None:
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
        mensaje = recibidos[0]
        assert mensaje["tipo"] == "pregunta_presentada"
        assert mensaje["pregunta_actual_indice"] == 1
        assert set(mensaje["pregunta"]) == {"pregunta_id", "enunciado", "tipo"}
        assert mensaje["pregunta"]["tipo"] == "opcion_multiple"
        assert "opciones" not in mensaje["pregunta"]
