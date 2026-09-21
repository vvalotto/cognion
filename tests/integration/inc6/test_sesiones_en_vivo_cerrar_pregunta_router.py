"""Tests HTTP + WebSocket de `POST /sesiones-en-vivo/{sesion_id}/cerrar-pregunta` (US-6.2.5).

Cubre los escenarios de `tests/features/inc6/US-6.2.5-cerrar-pregunta-en-vivo.feature` contra la
app real y la base de datos local.
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
    finalizar_sesion,
    headers_de,
    iniciar_sesion,
    mostrar_opciones,
    pregunta_actual_de,
    preparar_sesion,
    unirse_a_sesion,
)

CORRECTA = {"opcion_indice": 1}
INCORRECTA = {"opcion_indice": 0}


def _cliente() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _docente() -> dict[str, str]:
    return headers_de(uuid.uuid4(), TipoPerfil.DOCENTE)


def _url(sesion_id: str) -> str:
    return f"/sesiones-en-vivo/{sesion_id}/cerrar-pregunta"


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


async def _sesion_lista(mostrar: bool = True) -> tuple[str, str]:
    """Sesión iniciada (opción múltiple, "B" correcta), con opciones mostradas si se pide."""
    sesion_id, comision_id = await preparar_sesion(opcion_multiple=True)
    await iniciar_sesion(sesion_id)
    if mostrar:
        await mostrar_opciones(sesion_id)
    return sesion_id, comision_id


async def _responder(sesion_id: str, comision_id: str, contenido: dict) -> str:
    """Crea un Estudiante, lo une y responde; devuelve su `estudiante_id`."""
    estudiante_id, headers = await crear_estudiante(comision_id)
    await unirse_a_sesion(sesion_id, headers)
    pregunta_id = await pregunta_actual_de(sesion_id)
    async with _cliente() as client:
        respuesta = await client.post(
            f"/sesiones-en-vivo/{sesion_id}/responder",
            json={"pregunta_id": pregunta_id, "contenido": contenido},
            headers=headers,
        )
    assert respuesta.status_code == 200, respuesta.text
    return estudiante_id


class TestCerrarPreguntaAPIIntegration:
    async def test_cierre_exitoso_persiste_el_evento_minimo(self, session):
        sesion_id, comision_id = await _sesion_lista()
        await _responder(sesion_id, comision_id, CORRECTA)

        async with _cliente() as client:
            response = await client.post(_url(sesion_id), headers=_docente())

        assert response.status_code == 200
        assert response.json()["estado"] == "EnCurso"
        eventos = await _eventos_de_sesion(session, sesion_id)
        assert eventos[-1].event_type == "PreguntaEnVivoCerrada"
        assert set(eventos[-1].payload) == {
            "sesion_id",
            "pregunta_actual_indice",
            "pregunta_id",
            "ocurrido_en",
        }

    async def test_despues_de_cerrar_no_se_puede_responder(self):
        sesion_id, comision_id = await _sesion_lista()
        async with _cliente() as client:
            await client.post(_url(sesion_id), headers=_docente())
        estudiante_id, headers = await crear_estudiante(comision_id)
        await unirse_a_sesion(sesion_id, headers)

        async with _cliente() as client:
            response = await client.post(
                f"/sesiones-en-vivo/{sesion_id}/responder",
                json={
                    "pregunta_id": await pregunta_actual_de(sesion_id),
                    "contenido": CORRECTA,
                },
                headers=headers,
            )

        assert response.status_code == 422
        assert estudiante_id

    async def test_cerrar_sin_ninguna_respuesta_se_acepta(self):
        sesion_id, _ = await _sesion_lista()

        async with _cliente() as client:
            response = await client.post(_url(sesion_id), headers=_docente())

        assert response.status_code == 200

    async def test_rechazo_si_las_opciones_no_se_mostraron(self, session):
        sesion_id, _ = await _sesion_lista(mostrar=False)

        async with _cliente() as client:
            response = await client.post(_url(sesion_id), headers=_docente())

        assert response.status_code == 422
        assert "opciones" in response.json()["detail"]
        assert len(await _eventos_de_sesion(session, sesion_id)) == 2

    async def test_rechazo_si_ya_estaba_cerrada(self, session):
        sesion_id, _ = await _sesion_lista()
        async with _cliente() as client:
            await client.post(_url(sesion_id), headers=_docente())
            response = await client.post(_url(sesion_id), headers=_docente())

        assert response.status_code == 422
        assert len(await _eventos_de_sesion(session, sesion_id)) == 4

    async def test_rechazo_si_la_sesion_esta_en_espera(self):
        sesion_id, _ = await preparar_sesion()

        async with _cliente() as client:
            response = await client.post(_url(sesion_id), headers=_docente())

        assert response.status_code == 422
        assert "no está en curso" in response.json()["detail"]

    async def test_rechazo_si_la_sesion_esta_finalizada(self):
        sesion_id, _ = await _sesion_lista()
        await cerrar_pregunta_actual(sesion_id)
        await finalizar_sesion(sesion_id)

        async with _cliente() as client:
            response = await client.post(_url(sesion_id), headers=_docente())

        assert response.status_code == 422

    async def test_sesion_inexistente(self):
        async with _cliente() as client:
            response = await client.post(_url(str(uuid.uuid4())), headers=_docente())

        assert response.status_code == 404

    async def test_rechazo_por_rol_estudiante(self):
        sesion_id, comision_id = await _sesion_lista()
        _, headers = await crear_estudiante(comision_id)

        async with _cliente() as client:
            response = await client.post(_url(sesion_id), headers=headers)

        assert response.status_code == 403

    async def test_sin_token_se_rechaza(self):
        async with _cliente() as client:
            response = await client.post(_url(str(uuid.uuid4())))

        assert response.status_code in (401, 403)

    async def test_dos_cierres_simultaneos_dejan_ganar_a_uno_solo(self, session):
        sesion_id, _ = await _sesion_lista()

        async with _cliente() as client:
            respuestas = await asyncio.gather(
                client.post(_url(sesion_id), headers=_docente()),
                client.post(_url(sesion_id), headers=_docente()),
            )

        assert sorted(r.status_code for r in respuestas) == [200, 422]
        assert len(await _eventos_de_sesion(session, sesion_id)) == 4


class TestBroadcastATodosLosConectados:
    """Sincrónico: `TestClient` mantiene abiertos los WebSockets mientras el Docente cierra."""

    def test_docente_y_estudiante_reciben_el_mismo_mensaje_completo(self) -> None:
        sesion_id, comision_id = correr(_sesion_lista())
        acierto = correr(_responder(sesion_id, comision_id, CORRECTA))
        error = correr(_responder(sesion_id, comision_id, INCORRECTA))
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
        assert mensaje["tipo"] == "pregunta_cerrada"
        assert mensaje["pregunta_actual_indice"] == 0
        assert mensaje["respuesta_correcta"]["contenido"] == CORRECTA
        assert mensaje["respuesta_correcta"]["opciones"] == ["A", "B", "C", "D"]
        assert mensaje["distribucion"] == [
            {"opcion": "0", "cantidad": 1},
            {"opcion": "1", "cantidad": 1},
        ]
        posiciones = [(f["posicion"], f["estudiante_id"]) for f in mensaje["ranking"]]
        assert posiciones == [(1, acierto), (2, error)]
        assert (
            mensaje["ranking"][0]["puntaje_acumulado"] > mensaje["ranking"][1]["puntaje_acumulado"]
        )
        assert mensaje["ranking"][1]["puntaje_acumulado"] == 0
