"""Tests HTTP + WebSocket + concurrencia de `POST /sesiones-en-vivo/{id}/responder` (US-6.2.4).

Cubre los escenarios de `tests/features/inc6/US-6.2.4-responder-pregunta-en-vivo.feature` contra
la app real y la base de datos local.
"""

from __future__ import annotations

import asyncio
import uuid

from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.frameworks.event_store.sqlalchemy_event_store import (
    SQLAlchemyEventStore,
)
from src.app import app
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import SessionLocal
from tests.integration.inc6._helpers import (
    correr,
    crear_estudiante,
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


def _cliente() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _url(sesion_id: str) -> str:
    return f"/sesiones-en-vivo/{sesion_id}/responder"


async def _sesion_lista(mostrar: bool = True) -> tuple[str, str, str, dict[str, str], str]:
    """Sesión iniciada (opción múltiple, "B" correcta) con un Estudiante unido.

    Devuelve `(sesion_id, comision_id, estudiante_id, headers_estudiante, pregunta_id)`.
    """
    sesion_id, comision_id = await preparar_sesion(opcion_multiple=True)
    await iniciar_sesion(sesion_id)
    if mostrar:
        await mostrar_opciones(sesion_id)
    estudiante_id, headers = await crear_estudiante(comision_id)
    await unirse_a_sesion(sesion_id, headers)
    return sesion_id, comision_id, estudiante_id, headers, await pregunta_actual_de(sesion_id)


async def _responder(client, sesion_id, headers, pregunta_id, contenido):
    return await client.post(
        _url(sesion_id), json={"pregunta_id": pregunta_id, "contenido": contenido}, headers=headers
    )


async def _eventos_participacion(session, sesion_id: str, estudiante_id: str) -> list:
    resultado = await session.execute(
        text(
            "SELECT event_type, payload FROM events WHERE aggregate_type = 'ParticipacionEnVivo' "
            "AND payload->>'sesion_id' = :s AND payload->>'estudiante_id' = :e "
            "ORDER BY sequence_number"
        ),
        {"s": sesion_id, "e": estudiante_id},
    )
    return resultado.all()


class TestResponderAPIIntegration:
    async def test_respuesta_correcta_devuelve_feedback_y_persiste(self, session):
        sesion_id, _, estudiante_id, headers, pregunta_id = await _sesion_lista()

        async with _cliente() as client:
            response = await _responder(client, sesion_id, headers, pregunta_id, CORRECTA)

        assert response.status_code == 200
        cuerpo = response.json()
        assert cuerpo["es_correcta"] is True
        # dificultad medio (1.5) × importancia alto (2.0) × factor tiempo en [0.5, 1.0] × 1000
        assert 1500 <= cuerpo["puntaje"] <= 3000
        assert cuerpo["puntaje_acumulado"] == cuerpo["puntaje"]
        assert "ranking" not in cuerpo
        eventos = await _eventos_participacion(session, sesion_id, estudiante_id)
        assert [e.event_type for e in eventos] == ["EstudianteUnido", "RespuestaEnVivoRegistrada"]
        payload = eventos[1].payload
        assert payload["contenido"] == CORRECTA
        assert payload["es_correcta"] is True
        assert payload["tiempo_respuesta_segundos"] >= 0
        assert payload["puntaje"] == cuerpo["puntaje"]

    async def test_respuesta_incorrecta_puntua_cero(self):
        sesion_id, _, _, headers, pregunta_id = await _sesion_lista()

        async with _cliente() as client:
            response = await _responder(client, sesion_id, headers, pregunta_id, INCORRECTA)

        assert response.status_code == 200
        assert response.json() == {"es_correcta": False, "puntaje": 0, "puntaje_acumulado": 0}

    async def test_las_proyecciones_se_actualizan_junto_con_el_evento(self, session):
        sesion_id, _, estudiante_id, headers, pregunta_id = await _sesion_lista()

        async with _cliente() as client:
            cuerpo = (await _responder(client, sesion_id, headers, pregunta_id, CORRECTA)).json()

        ranking = await session.execute(
            text(
                "SELECT puntaje_acumulado FROM ranking_por_sesion "
                "WHERE sesion_id = :s AND estudiante_id = :e"
            ),
            {"s": sesion_id, "e": estudiante_id},
        )
        assert ranking.scalar_one() == cuerpo["puntaje_acumulado"]
        histograma = await session.execute(
            text(
                "SELECT opcion, cantidad FROM distribucion_por_pregunta "
                "WHERE sesion_id = :s AND pregunta_id = :p"
            ),
            {"s": sesion_id, "p": pregunta_id},
        )
        assert [(f.opcion, f.cantidad) for f in histograma.all()] == [("1", 1)]

    async def test_un_solo_intento_por_pregunta(self, session):
        sesion_id, _, estudiante_id, headers, pregunta_id = await _sesion_lista()
        async with _cliente() as client:
            primera = await _responder(client, sesion_id, headers, pregunta_id, CORRECTA)
            segunda = await _responder(client, sesion_id, headers, pregunta_id, INCORRECTA)

        assert segunda.status_code == 422
        assert "Ya registraste" in segunda.json()["detail"]
        assert len(await _eventos_participacion(session, sesion_id, estudiante_id)) == 2
        ranking = await session.execute(
            text("SELECT puntaje_acumulado FROM ranking_por_sesion WHERE estudiante_id = :e"),
            {"e": estudiante_id},
        )
        assert ranking.scalar_one() == primera.json()["puntaje_acumulado"]

    async def test_tiempo_agotado(self, session):
        sesion_id, comision_id = await preparar_sesion(opcion_multiple=True)
        await iniciar_sesion(sesion_id)
        await sembrar_opciones_mostradas_hace(sesion_id, 300)
        estudiante_id, headers = await crear_estudiante(comision_id)
        await unirse_a_sesion(sesion_id, headers)
        pregunta_id = await pregunta_actual_de(sesion_id)

        async with _cliente() as client:
            response = await _responder(client, sesion_id, headers, pregunta_id, CORRECTA)

        assert response.status_code == 422
        assert "fuera del tiempo límite" in response.json()["detail"]
        assert len(await _eventos_participacion(session, sesion_id, estudiante_id)) == 1

    async def test_opciones_no_mostradas_todavia(self):
        sesion_id, _, _, headers, pregunta_id = await _sesion_lista(mostrar=False)

        async with _cliente() as client:
            response = await _responder(client, sesion_id, headers, pregunta_id, CORRECTA)

        assert response.status_code == 422
        assert "todavía no se mostraron" in response.json()["detail"]

    async def test_pregunta_ya_cerrada(self):
        sesion_id, _, _, headers, pregunta_id = await _sesion_lista()
        async with SessionLocal() as s:
            store = SQLAlchemyEventStore(s)
            eventos = await store.load("ActividadEvaluativaEnVivo", uuid.UUID(sesion_id))
            await store.append(
                "ActividadEvaluativaEnVivo",
                uuid.UUID(sesion_id),
                len(eventos),
                [EventoParaAlmacenar("PreguntaEnVivoCerrada", {"sesion_id": sesion_id})],
            )

        async with _cliente() as client:
            response = await _responder(client, sesion_id, headers, pregunta_id, CORRECTA)

        assert response.status_code == 422
        assert "ya fue cerrada" in response.json()["detail"]

    async def test_pregunta_que_no_es_la_actual(self):
        sesion_id, _, _, headers, _ = await _sesion_lista()

        async with _cliente() as client:
            response = await _responder(client, sesion_id, headers, str(uuid.uuid4()), CORRECTA)

        assert response.status_code == 422
        assert "no es la pregunta actual" in response.json()["detail"]

    async def test_estudiante_que_no_se_unio(self):
        sesion_id, comision_id = await preparar_sesion(opcion_multiple=True)
        await iniciar_sesion(sesion_id)
        await mostrar_opciones(sesion_id)
        _, headers = await crear_estudiante(comision_id)

        async with _cliente() as client:
            response = await _responder(
                client, sesion_id, headers, await pregunta_actual_de(sesion_id), CORRECTA
            )

        assert response.status_code == 404

    async def test_sesion_inexistente(self):
        _, comision_id = await preparar_sesion(opcion_multiple=True)
        _, headers = await crear_estudiante(comision_id)

        async with _cliente() as client:
            response = await _responder(
                client, str(uuid.uuid4()), headers, str(uuid.uuid4()), CORRECTA
            )

        assert response.status_code == 404

    async def test_rechazo_por_rol_docente(self):
        sesion_id, _, _, _, pregunta_id = await _sesion_lista()

        async with _cliente() as client:
            response = await _responder(
                client,
                sesion_id,
                headers_de(uuid.uuid4(), TipoPerfil.DOCENTE),
                pregunta_id,
                CORRECTA,
            )

        assert response.status_code == 403

    async def test_sin_token_se_rechaza(self):
        async with _cliente() as client:
            response = await client.post(
                _url(str(uuid.uuid4())),
                json={"pregunta_id": str(uuid.uuid4()), "contenido": CORRECTA},
            )

        assert response.status_code in (401, 403)

    async def test_contenido_con_shape_invalido_se_rechaza_en_el_borde(self):
        sesion_id, _, _, headers, pregunta_id = await _sesion_lista()

        async with _cliente() as client:
            responses = [
                await _responder(client, sesion_id, headers, pregunta_id, contenido)
                for contenido in ({}, {"opcion_indice": "1"}, {"valor": 1}, {"opcion_indice": True})
            ]

        assert [r.status_code for r in responses] == [422, 422, 422, 422]


class TestConcurrenciaReal:
    async def test_doble_envio_simultaneo_registra_uno_solo(self, session):
        sesion_id, _, estudiante_id, headers, pregunta_id = await _sesion_lista()

        async with _cliente() as client:
            respuestas = await asyncio.gather(
                _responder(client, sesion_id, headers, pregunta_id, CORRECTA),
                _responder(client, sesion_id, headers, pregunta_id, CORRECTA),
            )

        assert sorted(r.status_code for r in respuestas) == [200, 422]
        assert len(await _eventos_participacion(session, sesion_id, estudiante_id)) == 2
        histograma = await session.execute(
            text(
                "SELECT cantidad FROM distribucion_por_pregunta "
                "WHERE sesion_id = :s AND pregunta_id = :p AND opcion = '1'"
            ),
            {"s": sesion_id, "p": pregunta_id},
        )
        assert histograma.scalar_one() == 1  # la proyección del perdedor se descartó
        ranking = await session.execute(
            text("SELECT puntaje_acumulado FROM ranking_por_sesion WHERE estudiante_id = :e"),
            {"e": estudiante_id},
        )
        assert ranking.scalar_one() == next(
            r.json()["puntaje"] for r in respuestas if r.status_code == 200
        )

    async def test_sesenta_respuestas_simultaneas_no_pierden_ninguna(self, session):
        sesion_id, comision_id = await preparar_sesion(opcion_multiple=True)
        await iniciar_sesion(sesion_id)
        pregunta_id = await pregunta_actual_de(sesion_id)
        estudiantes = await asyncio.gather(*(crear_estudiante(comision_id) for _ in range(60)))
        await asyncio.gather(*(unirse_a_sesion(sesion_id, h) for _, h in estudiantes))
        # Recién ahora arranca el temporizador: crear 60 cuentas (bcrypt) tarda más que el límite.
        await mostrar_opciones(sesion_id)

        async with _cliente() as client:
            respuestas = await asyncio.gather(
                *(_responder(client, sesion_id, h, pregunta_id, CORRECTA) for _, h in estudiantes)
            )

        assert [r.status_code for r in respuestas] == [200] * 60
        histograma = await session.execute(
            text(
                "SELECT cantidad FROM distribucion_por_pregunta "
                "WHERE sesion_id = :s AND pregunta_id = :p AND opcion = '1'"
            ),
            {"s": sesion_id, "p": pregunta_id},
        )
        assert histograma.scalar_one() == 60
        total = await session.execute(
            text(
                "SELECT COUNT(*), SUM(puntaje_acumulado) FROM ranking_por_sesion WHERE sesion_id = :s"
            ),
            {"s": sesion_id},
        )
        filas, suma = total.one()
        assert filas == 60
        assert suma == sum(r.json()["puntaje"] for r in respuestas)


class TestBroadcastDelConteo:
    """Sincrónico: `TestClient` mantiene abiertos los WebSockets mientras el Estudiante responde."""

    def test_todos_los_conectados_reciben_el_conteo_sin_desglose(self) -> None:
        sesion_id, comision_id = correr(preparar_sesion(opcion_multiple=True))
        correr(iniciar_sesion(sesion_id))
        correr(mostrar_opciones(sesion_id))
        _, headers = correr(crear_estudiante(comision_id))
        correr(unirse_a_sesion(sesion_id, headers))
        pregunta_id = correr(pregunta_actual_de(sesion_id))
        token_docente = headers_de(uuid.uuid4(), TipoPerfil.DOCENTE)["Authorization"].split()[1]
        token_estudiante = headers["Authorization"].split()[1]

        with TestClient(app) as client:
            with (
                client.websocket_connect(
                    f"/sesiones-en-vivo/{sesion_id}/canal?token={token_docente}"
                ) as ws_docente,
                client.websocket_connect(
                    f"/sesiones-en-vivo/{sesion_id}/canal?token={token_estudiante}"
                ) as ws_estudiante,
            ):
                response = client.post(
                    _url(sesion_id),
                    json={"pregunta_id": pregunta_id, "contenido": CORRECTA},
                    headers=headers,
                )
                assert response.status_code == 200
                recibidos = [ws_docente.receive_json(), ws_estudiante.receive_json()]

        for mensaje in recibidos:
            assert mensaje == {
                "tipo": "conteo_respuestas_actualizado",
                "pregunta_actual_indice": 0,
                "cantidad_respuestas": 1,
            }
