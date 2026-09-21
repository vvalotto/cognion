"""Verificación de la sesión en vivo completa de punta a punta (US-6.2.9, RF-08/09/10).

No agrega código de producción: recorre la API real, la DB local y WebSockets reales de punta a
punta. La medición del RNF de rendimiento vive aparte (`tests/uat/inc6/medir_rendimiento_cierre.py`)
porque depende de la máquina y no debe correr en cada suite.
"""

from __future__ import annotations

import asyncio
import uuid
from contextlib import ExitStack

from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from src.app import app
from src.shared.entities.tipo_perfil import TipoPerfil
from tests.integration.inc6._helpers import (
    correr,
    crear_estudiantes,
    headers_de,
    iniciar_sesion,
    mostrar_opciones,
    pregunta_actual_de,
    preparar_sesion,
    sembrar_opciones_mostradas_hace,
    unirse_a_sesion,
)

CORRECTA = {"opcion_indice": 1}
INCORRECTA = {"opcion_indice": 0}


def _docente() -> dict[str, str]:
    return headers_de(uuid.uuid4(), TipoPerfil.DOCENTE)


def _token(headers: dict[str, str]) -> str:
    return headers["Authorization"].split()[1]


def _canal(sesion_id: str, headers: dict[str, str]) -> str:
    return f"/sesiones-en-vivo/{sesion_id}/canal?token={_token(headers)}"


def _leer(ws, tipo: str) -> dict:
    """Lee del WebSocket hasta el primer mensaje de `tipo` (ya está en cola: no bloquea)."""
    while True:
        mensaje = ws.receive_json()
        if mensaje["tipo"] == tipo:
            return mensaje


def _cliente_async() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


class TestSesionCompletaDePuntaAPunta:
    """Escenario 1: 5 Estudiantes, 3 preguntas, finalización y ranking final."""

    def test_recorrido_completo_con_broadcast_a_todos_los_conectados(self) -> None:
        sesion_id, comision_id = correr(preparar_sesion(opcion_multiple=True))
        estudiantes = correr(crear_estudiantes(comision_id, 5))
        docente = _docente()
        base = f"/sesiones-en-vivo/{sesion_id}"
        puntos_por_estudiante = {estudiante_id: 0 for estudiante_id, _ in estudiantes}

        with TestClient(app) as client, ExitStack() as stack:
            sockets = [
                stack.enter_context(client.websocket_connect(_canal(sesion_id, h)))
                for h in [docente] + [h for _, h in estudiantes]
            ]
            for _, headers in estudiantes:
                assert client.post(f"{base}/unirse", headers=headers).status_code == 200
            assert client.post(f"{base}/iniciar", headers=docente).status_code == 200
            presentadas = [_leer(ws, "pregunta_presentada") for ws in sockets]
            assert all(m == presentadas[0] for m in presentadas)
            assert presentadas[0]["pregunta_actual_indice"] == 0

            for indice in range(3):
                if indice > 0:
                    assert client.post(f"{base}/avanzar", headers=docente).status_code == 200
                    assert all(
                        _leer(ws, "pregunta_presentada")["pregunta_actual_indice"] == indice
                        for ws in sockets
                    )
                assert client.post(f"{base}/mostrar-opciones", headers=docente).status_code == 200
                assert all(_leer(ws, "opciones_mostradas")["opciones"] for ws in sockets)

                pregunta_id = correr(pregunta_actual_de_indice(sesion_id, indice))
                for posicion, (estudiante_id, headers) in enumerate(estudiantes):
                    contenido = CORRECTA if posicion % 2 == 0 else INCORRECTA
                    respuesta = client.post(
                        f"{base}/responder",
                        json={"pregunta_id": pregunta_id, "contenido": contenido},
                        headers=headers,
                    )
                    assert respuesta.status_code == 200, respuesta.text
                    puntos_por_estudiante[estudiante_id] += respuesta.json()["puntaje"]

                assert client.post(f"{base}/cerrar-pregunta", headers=docente).status_code == 200
                cierres = [_leer(ws, "pregunta_cerrada") for ws in sockets]
                assert all(m == cierres[0] for m in cierres)
                acumulado = {
                    r["estudiante_id"]: r["puntaje_acumulado"] for r in cierres[0]["ranking"]
                }
                assert acumulado == puntos_por_estudiante

            # El Estudiante ve el ranking solo después de finalizar.
            _, un_estudiante = estudiantes[0]
            assert client.get(f"{base}/ranking", headers=un_estudiante).status_code == 403
            assert client.post(f"{base}/finalizar", headers=docente).status_code == 200
            finales = [_leer(ws, "sesion_finalizada") for ws in sockets]
            assert all(m == finales[0] for m in finales)
            ranking_final = client.get(f"{base}/ranking", headers=un_estudiante)

        assert ranking_final.status_code == 200
        puntajes = [fila["puntaje_acumulado"] for fila in finales[0]["ranking"]]
        assert puntajes == sorted(puntajes, reverse=True)
        assert {r["estudiante_id"]: r["puntaje_acumulado"] for r in finales[0]["ranking"]} == (
            puntos_por_estudiante
        )
        assert ranking_final.json() == finales[0]["ranking"]
        assert sum(puntajes) == sum(puntos_por_estudiante.values()) > 0


async def pregunta_actual_de_indice(sesion_id: str, indice: int) -> str:
    """Devuelve el `pregunta_id` de la pregunta en la posición `indice` del set de la sesión."""
    from src.actividad_evaluativa.frameworks.event_store.sqlalchemy_event_store import (
        SQLAlchemyEventStore,
    )
    from src.shared.frameworks.db import SessionLocal

    async with SessionLocal() as session:
        eventos = await SQLAlchemyEventStore(session).load(
            "ActividadEvaluativaEnVivo", uuid.UUID(sesion_id)
        )
    return eventos[0].payload["preguntas"][indice]["pregunta_id"]


class TestRespuestasSimultaneas:
    """Escenario 3: 60 Estudiantes responden a la vez."""

    async def test_las_60_se_registran_el_histograma_suma_60_y_el_ranking_las_refleja(
        self, session
    ):
        sesion_id, comision_id = await preparar_sesion(opcion_multiple=True)
        estudiantes = await crear_estudiantes(comision_id, 60)
        for _, headers in estudiantes:
            await unirse_a_sesion(sesion_id, headers)
        await iniciar_sesion(sesion_id)
        await mostrar_opciones(sesion_id)
        pregunta_id = await pregunta_actual_de(sesion_id)

        async with _cliente_async() as client:
            respuestas = await asyncio.gather(
                *[
                    client.post(
                        f"/sesiones-en-vivo/{sesion_id}/responder",
                        json={
                            "pregunta_id": pregunta_id,
                            "contenido": CORRECTA if posicion % 3 else INCORRECTA,
                        },
                        headers=headers,
                    )
                    for posicion, (_, headers) in enumerate(estudiantes)
                ]
            )
            ranking = await client.get(f"/sesiones-en-vivo/{sesion_id}/ranking", headers=_docente())

        assert [r.status_code for r in respuestas] == [200] * 60
        resultado = await session.execute(
            text(
                "SELECT COALESCE(SUM(cantidad), 0) FROM distribucion_por_pregunta WHERE sesion_id = :s"
            ),
            {"s": sesion_id},
        )
        assert resultado.scalar_one() == 60
        esperado = {
            estudiante_id: respuesta.json()["puntaje_acumulado"]
            for (estudiante_id, _), respuesta in zip(estudiantes, respuestas, strict=True)
        }
        assert ranking.status_code == 200
        assert {r["estudiante_id"]: r["puntaje_acumulado"] for r in ranking.json()} == esperado
        assert len(ranking.json()) == 60


class TestReconexion:
    """Escenario 4: un Estudiante pierde la conexión con la pregunta abierta y vuelve."""

    def test_recupera_pregunta_tiempo_y_avance_sin_perder_su_participacion(self) -> None:
        sesion_id, comision_id = correr(preparar_sesion(opcion_multiple=True))
        ((estudiante_id, headers),) = correr(crear_estudiantes(comision_id, 1))
        docente = _docente()
        base = f"/sesiones-en-vivo/{sesion_id}"

        with TestClient(app) as client:
            assert client.post(f"{base}/unirse", headers=headers).status_code == 200
            assert client.post(f"{base}/iniciar", headers=docente).status_code == 200
            assert client.post(f"{base}/mostrar-opciones", headers=docente).status_code == 200
            pregunta_id = correr(pregunta_actual_de(sesion_id))
            with client.websocket_connect(_canal(sesion_id, headers)):
                respuesta = client.post(
                    f"{base}/responder",
                    json={"pregunta_id": pregunta_id, "contenido": CORRECTA},
                    headers=headers,
                )
                assert respuesta.status_code == 200
            # La conexión se cayó; la sesión sigue con la pregunta abierta.

            with client.websocket_connect(_canal(sesion_id, headers)) as ws:
                estado = client.get(base, headers=headers).json()
                unirse_de_nuevo = client.post(f"{base}/unirse", headers=headers)
                assert client.post(f"{base}/cerrar-pregunta", headers=docente).status_code == 200
                cierre = _leer(ws, "pregunta_cerrada")

        assert estado["pregunta_actual"]["pregunta_id"] == pregunta_id
        assert estado["pregunta_actual"]["opciones"] == ["A", "B", "C", "D"]
        assert estado["opciones_mostradas_en"] is not None
        assert estado["tiempo_limite_por_pregunta_segundos"] == 30
        assert estado["ya_respondio"] is True
        assert estado["puntaje_acumulado"] == respuesta.json()["puntaje_acumulado"] > 0
        assert unirse_de_nuevo.status_code == 200
        assert unirse_de_nuevo.json()["estudiante_id"] == estudiante_id
        # Volvió a suscribirse al canal: recibe el siguiente broadcast.
        assert cierre["ranking"][0]["estudiante_id"] == estudiante_id


class TestRespuestaTardia:
    """Escenario 5: la respuesta fuera del tiempo límite se descarta y no toca el ranking."""

    async def test_tiempo_agotado_no_altera_el_ranking(self, session):
        sesion_id, comision_id = await preparar_sesion(opcion_multiple=True)
        await iniciar_sesion(sesion_id)
        await sembrar_opciones_mostradas_hace(sesion_id, 300)
        ((estudiante_id, headers),) = await crear_estudiantes(comision_id, 1)
        await unirse_a_sesion(sesion_id, headers)
        pregunta_id = await pregunta_actual_de(sesion_id)

        async with _cliente_async() as client:
            respuesta = await client.post(
                f"/sesiones-en-vivo/{sesion_id}/responder",
                json={"pregunta_id": pregunta_id, "contenido": CORRECTA},
                headers=headers,
            )
            ranking = await client.get(f"/sesiones-en-vivo/{sesion_id}/ranking", headers=_docente())

        assert respuesta.status_code == 422
        assert "fuera del tiempo límite" in respuesta.json()["detail"]
        assert ranking.json() == [
            {"posicion": 1, "estudiante_id": estudiante_id, "puntaje_acumulado": 0}
        ]
        resultado = await session.execute(
            text(
                "SELECT count(*) FROM events WHERE aggregate_type = 'ParticipacionEnVivo' "
                "AND payload->>'sesion_id' = :s AND event_type = 'RespuestaEnVivoRegistrada'"
            ),
            {"s": sesion_id},
        )
        assert resultado.scalar_one() == 0
