"""Tests HTTP de `GET /sesiones-en-vivo/{id}`, `.../participantes` y `.../ranking` (US-6.2.8).

Cubre los escenarios de `tests/features/inc6/US-6.2.8-consultar-estado-sesion-en-vivo.feature`
contra la app real y la base de datos local.
"""

from __future__ import annotations

import uuid

from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from src.app import app
from src.shared.entities.tipo_perfil import TipoPerfil
from tests.integration.inc6._helpers import (
    cerrar_pregunta_actual,
    crear_estudiante,
    finalizar_sesion,
    headers_de,
    iniciar_sesion,
    mostrar_opciones,
    pregunta_actual_de,
    preparar_sesion,
    unirse_a_sesion,
)


def _cliente() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _docente() -> dict[str, str]:
    return headers_de(uuid.uuid4(), TipoPerfil.DOCENTE)


async def _get(ruta: str, headers: dict[str, str]):
    async with _cliente() as client:
        return await client.get(ruta, headers=headers)


async def _responder(sesion_id: str, headers, pregunta_id: str, opcion: int) -> dict:
    async with _cliente() as client:
        respuesta = await client.post(
            f"/sesiones-en-vivo/{sesion_id}/responder",
            json={"pregunta_id": pregunta_id, "contenido": {"opcion_indice": opcion}},
            headers=headers,
        )
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


async def _contar_eventos(session, sesion_id: str) -> int:
    resultado = await session.execute(
        text("SELECT count(*) FROM events WHERE aggregate_id = :id"), {"id": sesion_id}
    )
    return resultado.scalar_one()


class TestEstadoAPIIntegration:
    async def test_sesion_en_espera_sin_pregunta_actual(self):
        sesion_id, _ = await preparar_sesion(opcion_multiple=True)

        response = await _get(f"/sesiones-en-vivo/{sesion_id}", _docente())

        assert response.status_code == 200
        cuerpo = response.json()
        assert cuerpo["estado"] == "EnEspera"
        assert cuerpo["pregunta_actual"] is None
        assert cuerpo["cantidad_preguntas"] == 5
        assert cuerpo["ya_respondio"] is None

    async def test_enunciado_sin_opciones_ni_correcta(self):
        sesion_id, comision_id = await preparar_sesion(opcion_multiple=True)
        await iniciar_sesion(sesion_id)
        _, headers = await crear_estudiante(comision_id)

        cuerpo = (await _get(f"/sesiones-en-vivo/{sesion_id}", headers)).json()

        pregunta = cuerpo["pregunta_actual"]
        assert pregunta["enunciado"].startswith("Pregunta")
        assert pregunta["tipo"] == "opcion_multiple"
        assert pregunta["opciones"] is None
        assert pregunta["respuesta_correcta"] is None
        assert cuerpo["opciones_mostradas"] is False

    async def test_con_opciones_mostradas_expone_referencia_de_tiempo(self):
        sesion_id, comision_id = await preparar_sesion(opcion_multiple=True)
        await iniciar_sesion(sesion_id)
        await mostrar_opciones(sesion_id)
        _, headers = await crear_estudiante(comision_id)

        cuerpo = (await _get(f"/sesiones-en-vivo/{sesion_id}", headers)).json()

        assert cuerpo["pregunta_actual"]["opciones"] == ["A", "B", "C", "D"]
        assert cuerpo["pregunta_actual"]["respuesta_correcta"] is None
        assert cuerpo["opciones_mostradas_en"] is not None
        assert cuerpo["tiempo_limite_por_pregunta_segundos"] == 30

    async def test_con_la_pregunta_cerrada_expone_la_correcta(self):
        sesion_id, comision_id = await preparar_sesion(opcion_multiple=True)
        await iniciar_sesion(sesion_id)
        await mostrar_opciones(sesion_id)
        await cerrar_pregunta_actual(sesion_id)
        _, headers = await crear_estudiante(comision_id)

        cuerpo = (await _get(f"/sesiones-en-vivo/{sesion_id}", headers)).json()

        assert cuerpo["pregunta_actual_cerrada"] is True
        assert cuerpo["pregunta_actual"]["respuesta_correcta"]["contenido"] == {"opcion_indice": 1}

    async def test_el_estudiante_ve_su_propio_avance(self):
        sesion_id, comision_id = await preparar_sesion(opcion_multiple=True)
        await iniciar_sesion(sesion_id)
        _, headers = await crear_estudiante(comision_id)
        await unirse_a_sesion(sesion_id, headers)
        await mostrar_opciones(sesion_id)
        antes = (await _get(f"/sesiones-en-vivo/{sesion_id}", headers)).json()
        feedback = await _responder(sesion_id, headers, await pregunta_actual_de(sesion_id), 1)

        despues = (await _get(f"/sesiones-en-vivo/{sesion_id}", headers)).json()

        assert antes["ya_respondio"] is False and antes["puntaje_acumulado"] == 0
        assert despues["ya_respondio"] is True
        assert despues["puntaje_acumulado"] == feedback["puntaje_acumulado"] > 0

    async def test_total_participantes_y_cantidad_respuestas(self):
        sesion_id, comision_id = await preparar_sesion(opcion_multiple=True)
        await iniciar_sesion(sesion_id)
        await mostrar_opciones(sesion_id)
        pregunta_id = await pregunta_actual_de(sesion_id)
        for _ in range(3):
            _, headers = await crear_estudiante(comision_id)
            await unirse_a_sesion(sesion_id, headers)
            await _responder(sesion_id, headers, pregunta_id, 1)
        _, headers_sin_responder = await crear_estudiante(comision_id)
        await unirse_a_sesion(sesion_id, headers_sin_responder)

        cuerpo = (await _get(f"/sesiones-en-vivo/{sesion_id}", _docente())).json()

        assert cuerpo["total_participantes"] == 4
        assert cuerpo["cantidad_respuestas"] == 3

    async def test_sin_pregunta_actual_cantidad_respuestas_es_cero(self):
        sesion_id, _ = await preparar_sesion(opcion_multiple=True)

        cuerpo = (await _get(f"/sesiones-en-vivo/{sesion_id}", _docente())).json()

        assert cuerpo["cantidad_respuestas"] == 0
        assert cuerpo["resultado_pregunta"] is None

    async def test_docente_recupera_histograma_y_ranking_con_la_pregunta_cerrada(self):
        sesion_id, comision_id = await preparar_sesion(opcion_multiple=True)
        await iniciar_sesion(sesion_id)
        await mostrar_opciones(sesion_id)
        _, headers = await crear_estudiante(comision_id)
        await unirse_a_sesion(sesion_id, headers)
        await _responder(sesion_id, headers, await pregunta_actual_de(sesion_id), 1)
        await cerrar_pregunta_actual(sesion_id)

        cuerpo = (await _get(f"/sesiones-en-vivo/{sesion_id}", _docente())).json()

        resultado = cuerpo["resultado_pregunta"]
        assert resultado is not None
        assert resultado["distribucion"] == [{"opcion": "1", "cantidad": 1}]
        assert len(resultado["ranking"]) == 1
        assert resultado["ranking"][0]["nombre"] == "Estudiante"

    async def test_sin_resultado_con_la_pregunta_abierta(self):
        sesion_id, _ = await preparar_sesion(opcion_multiple=True)
        await iniciar_sesion(sesion_id)
        await mostrar_opciones(sesion_id)

        cuerpo = (await _get(f"/sesiones-en-vivo/{sesion_id}", _docente())).json()

        assert cuerpo["resultado_pregunta"] is None

    async def test_el_estudiante_nunca_recibe_resultado_pregunta(self):
        sesion_id, comision_id = await preparar_sesion(opcion_multiple=True)
        await iniciar_sesion(sesion_id)
        await mostrar_opciones(sesion_id)
        _, headers = await crear_estudiante(comision_id)
        await unirse_a_sesion(sesion_id, headers)
        await _responder(sesion_id, headers, await pregunta_actual_de(sesion_id), 1)
        await cerrar_pregunta_actual(sesion_id)

        cuerpo = (await _get(f"/sesiones-en-vivo/{sesion_id}", headers)).json()

        assert cuerpo["resultado_pregunta"] is None

    async def test_estado_anterior_sigue_funcionando(self):
        sesion_id, _ = await preparar_sesion(opcion_multiple=True)

        cuerpo = (await _get(f"/sesiones-en-vivo/{sesion_id}", _docente())).json()

        assert cuerpo["estado"] == "EnEspera"
        assert cuerpo["pregunta_actual"] is None
        assert cuerpo["cantidad_preguntas"] == 5
        assert cuerpo["ya_respondio"] is None

    async def test_consultar_no_escribe_eventos(self, session):
        sesion_id, _ = await preparar_sesion(opcion_multiple=True)
        await iniciar_sesion(sesion_id)
        antes = await _contar_eventos(session, sesion_id)

        await _get(f"/sesiones-en-vivo/{sesion_id}", _docente())

        assert await _contar_eventos(session, sesion_id) == antes

    async def test_sesion_inexistente(self):
        response = await _get(f"/sesiones-en-vivo/{uuid.uuid4()}", _docente())

        assert response.status_code == 404

    async def test_sin_token_se_rechaza(self):
        async with _cliente() as client:
            response = await client.get(f"/sesiones-en-vivo/{uuid.uuid4()}")

        assert response.status_code in (401, 403)

    async def test_rol_administrador_se_rechaza(self):
        admin = headers_de(uuid.uuid4(), TipoPerfil.ADMINISTRADOR)

        response = await _get(f"/sesiones-en-vivo/{uuid.uuid4()}", admin)

        assert response.status_code == 403


class TestParticipantesAPIIntegration:
    async def test_lista_a_los_unidos_en_orden_de_union(self):
        sesion_id, comision_id = await preparar_sesion()
        ids = []
        for _ in range(3):
            estudiante_id, headers = await crear_estudiante(comision_id)
            await unirse_a_sesion(sesion_id, headers)
            ids.append(estudiante_id)

        response = await _get(f"/sesiones-en-vivo/{sesion_id}/participantes", _docente())

        assert response.status_code == 200
        assert [p["estudiante_id"] for p in response.json()] == ids

    async def test_sala_vacia(self):
        sesion_id, _ = await preparar_sesion()

        response = await _get(f"/sesiones-en-vivo/{sesion_id}/participantes", _docente())

        assert response.json() == []

    async def test_participante_trae_el_nombre_real_resuelto_contra_identidad(self):
        sesion_id, comision_id = await preparar_sesion()
        _, headers = await crear_estudiante(comision_id)
        await unirse_a_sesion(sesion_id, headers)

        response = await _get(f"/sesiones-en-vivo/{sesion_id}/participantes", _docente())

        assert response.json()[0]["nombre"] == "Estudiante"

    async def test_rechazo_por_rol_estudiante(self):
        sesion_id, comision_id = await preparar_sesion()
        _, headers = await crear_estudiante(comision_id)

        response = await _get(f"/sesiones-en-vivo/{sesion_id}/participantes", headers)

        assert response.status_code == 403

    async def test_sesion_inexistente(self):
        response = await _get(f"/sesiones-en-vivo/{uuid.uuid4()}/participantes", _docente())

        assert response.status_code == 404


class TestRankingAPIIntegration:
    async def _sesion_con_puntaje(self):
        sesion_id, comision_id = await preparar_sesion(opcion_multiple=True)
        await iniciar_sesion(sesion_id)
        estudiante_id, headers = await crear_estudiante(comision_id)
        await unirse_a_sesion(sesion_id, headers)
        await mostrar_opciones(sesion_id)
        feedback = await _responder(sesion_id, headers, await pregunta_actual_de(sesion_id), 1)
        return sesion_id, estudiante_id, headers, feedback["puntaje_acumulado"]

    async def test_docente_lo_ve_en_cualquier_momento(self):
        sesion_id, estudiante_id, _, puntaje = await self._sesion_con_puntaje()

        response = await _get(f"/sesiones-en-vivo/{sesion_id}/ranking", _docente())

        assert response.status_code == 200
        fila = response.json()[0]
        assert fila["posicion"] == 1
        assert fila["estudiante_id"] == estudiante_id
        assert fila["puntaje_acumulado"] == puntaje
        assert fila["nombre"] == "Estudiante"

    async def test_estudiante_no_lo_ve_hasta_que_finaliza(self):
        sesion_id, _, headers, puntaje = await self._sesion_con_puntaje()

        antes = await _get(f"/sesiones-en-vivo/{sesion_id}/ranking", headers)
        await cerrar_pregunta_actual(sesion_id)
        await finalizar_sesion(sesion_id)
        despues = await _get(f"/sesiones-en-vivo/{sesion_id}/ranking", headers)

        assert antes.status_code == 403
        assert despues.status_code == 200
        assert despues.json()[0]["puntaje_acumulado"] == puntaje

    async def test_sesion_inexistente(self):
        response = await _get(f"/sesiones-en-vivo/{uuid.uuid4()}/ranking", _docente())

        assert response.status_code == 404
