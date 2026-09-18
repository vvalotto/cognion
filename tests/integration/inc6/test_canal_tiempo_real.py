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

from uuid import uuid4

from fastapi.testclient import TestClient

from src.actividad_evaluativa.frameworks.dependencies import get_connection_manager
from src.app import app
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.security.jwt_pyjwt import PyJWTIssuer


def _token(rol: TipoPerfil = TipoPerfil.DOCENTE) -> str:
    return PyJWTIssuer().emitir(uuid4(), rol).token


def _url_canal(sesion_id, token: str | None) -> str:
    base = f"/sesiones-en-vivo/{sesion_id}/canal"
    return f"{base}?token={token}" if token is not None else base


class TestBroadcast:
    def test_dos_clientes_del_mismo_canal_reciben_el_mismo_mensaje(self) -> None:
        sesion_id = uuid4()
        with TestClient(app) as client:
            connection_manager = get_connection_manager()
            with (
                client.websocket_connect(_url_canal(sesion_id, _token())) as ws_1,
                client.websocket_connect(
                    _url_canal(sesion_id, _token(TipoPerfil.ESTUDIANTE))
                ) as ws_2,
            ):
                client.portal.call(
                    connection_manager.enviar_a_sesion, sesion_id, {"tipo": "prueba"}
                )

                assert ws_1.receive_json() == {"tipo": "prueba"}
                assert ws_2.receive_json() == {"tipo": "prueba"}


class TestAislamientoEntreCanales:
    def test_mensaje_de_una_sesion_no_llega_a_otra(self) -> None:
        sesion_a, sesion_b = uuid4(), uuid4()
        with TestClient(app) as client:
            connection_manager = get_connection_manager()
            with (
                client.websocket_connect(_url_canal(sesion_a, _token())) as ws_a,
                client.websocket_connect(_url_canal(sesion_b, _token())) as ws_b,
            ):
                client.portal.call(
                    connection_manager.enviar_a_sesion, sesion_a, {"tipo": "solo-a"}
                )
                client.portal.call(
                    connection_manager.enviar_a_sesion,
                    sesion_b,
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
        sesion_id = uuid4()
        with TestClient(app) as client:
            connection_manager = get_connection_manager()
            with client.websocket_connect(_url_canal(sesion_id, _token())) as ws_sobreviviente:
                with client.websocket_connect(_url_canal(sesion_id, _token())):
                    pass  # se desconecta al salir del `with`

                client.portal.call(
                    connection_manager.enviar_a_sesion,
                    sesion_id,
                    {"tipo": "post-desconexion"},
                )

                assert ws_sobreviviente.receive_json() == {"tipo": "post-desconexion"}
