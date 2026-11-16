"""Tests de integración del canal de tiempo real por WebSocket (`US-6.1.1`).

Usa `TestClient.websocket_connect` (Starlette) contra la app real — verifica el contrato
completo: autenticación por query param, broadcast, aislamiento entre canales y resiliencia a
la desconexión de un cliente.

Tests sincrónicos (no `async def`): `TestClient` corre la app en un thread propio con su
propio loop de eventos (`client.portal`, expuesto al entrar al `with TestClient(app) as
client:`) — `client.portal.call(...)` ejecuta una corrutina en ese mismo loop, que es el que
también usan las conexiones WebSocket abiertas por ese cliente. Publicar directamente con
`asyncio.run(...)` desde el thread del test correría en un loop distinto y rompería los
objetos `WebSocket`, que no son thread-safe entre loops.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from src.actividad_evaluativa.frameworks.dependencies import get_connection_manager
from src.app import app
from src.shared.frameworks.db import SessionLocal
from tests.integration.inc6._helpers import (
    correr,
    crear_estudiante,
    headers_docente_de_sesion,
    preparar_sesion,
)


async def _limpiar_tablas() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM events"))
        await session.execute(text("DELETE FROM pregunta_plantilla"))
        await session.execute(text("DELETE FROM banco"))
        await session.execute(text("DELETE FROM comision_docentes"))
        await session.execute(text("DELETE FROM estudiante"))
        await session.execute(text("DELETE FROM comision"))
        await session.execute(text("DELETE FROM materia"))
        await session.execute(text("DELETE FROM administrador"))
        await session.execute(text("DELETE FROM docente"))
        await session.execute(text("DELETE FROM usuario"))
        await session.commit()


@pytest.fixture(autouse=True)
def limpiar_tablas():
    correr(_limpiar_tablas())
    yield
    correr(_limpiar_tablas())


def _token_docente(sesion_id: str) -> str:
    """Token del docente asignado a la comisión de la sesión (`US-12.1.1`)."""
    return correr(headers_docente_de_sesion(sesion_id))["Authorization"].split()[1]


def _token_estudiante(comision_id: str) -> str:
    """Token de un estudiante de la comisión indicada (`US-12.1.1`)."""
    _, headers = correr(crear_estudiante(comision_id))
    return headers["Authorization"].split()[1]


def _url_canal(sesion_id, token: str | None) -> str:
    base = f"/sesiones-en-vivo/{sesion_id}/canal"
    return f"{base}?token={token}" if token is not None else base


class TestBroadcast:
    def test_dos_clientes_del_mismo_canal_reciben_el_mismo_mensaje(self) -> None:
        sesion_id, comision_id = correr(preparar_sesion())
        token_docente = _token_docente(sesion_id)
        token_estudiante = _token_estudiante(comision_id)
        with TestClient(app) as client:
            connection_manager = get_connection_manager()
            with (
                client.websocket_connect(_url_canal(sesion_id, token_docente)) as ws_1,
                client.websocket_connect(_url_canal(sesion_id, token_estudiante)) as ws_2,
            ):
                client.portal.call(
                    connection_manager.enviar_a_sesion, UUID(sesion_id), {"tipo": "prueba"}
                )

                assert ws_1.receive_json() == {"tipo": "prueba"}
                assert ws_2.receive_json() == {"tipo": "prueba"}


class TestAislamientoEntreCanales:
    def test_mensaje_de_una_sesion_no_llega_a_otra(self) -> None:
        sesion_a, _ = correr(preparar_sesion())
        sesion_b, _ = correr(preparar_sesion())
        token_a, token_b = _token_docente(sesion_a), _token_docente(sesion_b)
        with TestClient(app) as client:
            connection_manager = get_connection_manager()
            with (
                client.websocket_connect(_url_canal(sesion_a, token_a)) as ws_a,
                client.websocket_connect(_url_canal(sesion_b, token_b)) as ws_b,
            ):
                client.portal.call(
                    connection_manager.enviar_a_sesion, UUID(sesion_a), {"tipo": "solo-a"}
                )
                client.portal.call(
                    connection_manager.enviar_a_sesion,
                    UUID(sesion_b),
                    {"tipo": "solo-b-para-cerrar"},
                )

                assert ws_a.receive_json() == {"tipo": "solo-a"}
                assert ws_b.receive_json() == {"tipo": "solo-b-para-cerrar"}


class TestRechazoDeConexion:
    def test_sin_token_se_rechaza_con_1008(self) -> None:
        sesion_id = uuid4()
        with TestClient(app) as client:
            try:
                with client.websocket_connect(_url_canal(sesion_id, None)):
                    raise AssertionError("La conexión debería haberse rechazado")
            except Exception as exc:  # noqa: BLE001 — capturamos WebSocketDisconnect
                assert type(exc).__name__ == "WebSocketDisconnect"
                assert getattr(exc, "code", None) == 1008

    def test_con_token_invalido_se_rechaza_con_1008(self) -> None:
        sesion_id = uuid4()
        with TestClient(app) as client:
            try:
                with client.websocket_connect(_url_canal(sesion_id, "token-invalido")):
                    raise AssertionError("La conexión debería haberse rechazado")
            except Exception as exc:  # noqa: BLE001
                assert type(exc).__name__ == "WebSocketDisconnect"
                assert getattr(exc, "code", None) == 1008


class TestDesconexion:
    def test_desconexion_de_un_cliente_no_rompe_el_broadcast_a_los_demas(self) -> None:
        sesion_id, comision_id = correr(preparar_sesion())
        token_docente = _token_docente(sesion_id)
        token_estudiante = _token_estudiante(comision_id)
        with TestClient(app) as client:
            connection_manager = get_connection_manager()
            with client.websocket_connect(_url_canal(sesion_id, token_docente)) as ws_sobreviviente:
                with client.websocket_connect(_url_canal(sesion_id, token_estudiante)):
                    pass  # se desconecta al salir del `with`

                client.portal.call(
                    connection_manager.enviar_a_sesion,
                    UUID(sesion_id),
                    {"tipo": "post-desconexion"},
                )

                assert ws_sobreviviente.receive_json() == {"tipo": "post-desconexion"}
