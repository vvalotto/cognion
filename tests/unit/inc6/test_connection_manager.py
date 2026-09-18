"""Tests unitarios de `ConnectionManager` (US-6.1.1).

Usa un doble en memoria de `WebSocket` — no hay dependencia real de FastAPI/Starlette en estos
tests, la verificación contra un WebSocket real ocurre en
`tests/integration/inc6/test_canal_tiempo_real.py` (`TestClient.websocket_connect`).
"""

from uuid import uuid4

from src.actividad_evaluativa.frameworks.websockets.connection_manager import ConnectionManager


class _FakeWebSocket:
    """Doble mínimo de `fastapi.WebSocket` — solo lo que `ConnectionManager` usa."""

    def __init__(self, *, falla_al_enviar: bool = False) -> None:
        self.aceptada = False
        self.mensajes_recibidos: list[dict] = []
        self._falla_al_enviar = falla_al_enviar

    async def accept(self) -> None:
        self.aceptada = True

    async def send_json(self, mensaje: dict) -> None:
        if self._falla_al_enviar:
            raise RuntimeError("conexión cerrada del lado del cliente")
        self.mensajes_recibidos.append(mensaje)


class TestConectar:
    async def test_acepta_el_handshake(self):
        manager = ConnectionManager()
        websocket = _FakeWebSocket()

        await manager.conectar(uuid4(), websocket)

        assert websocket.aceptada is True

    async def test_registra_varias_conexiones_del_mismo_canal(self):
        manager = ConnectionManager()
        sesion_id = uuid4()
        websocket_1, websocket_2 = _FakeWebSocket(), _FakeWebSocket()

        await manager.conectar(sesion_id, websocket_1)
        await manager.conectar(sesion_id, websocket_2)
        await manager.enviar_a_sesion(sesion_id, {"tipo": "prueba"})

        assert websocket_1.mensajes_recibidos == [{"tipo": "prueba"}]
        assert websocket_2.mensajes_recibidos == [{"tipo": "prueba"}]


class TestEnviarASesion:
    async def test_aislamiento_entre_canales(self):
        manager = ConnectionManager()
        sesion_a, sesion_b = uuid4(), uuid4()
        websocket_a, websocket_b = _FakeWebSocket(), _FakeWebSocket()
        await manager.conectar(sesion_a, websocket_a)
        await manager.conectar(sesion_b, websocket_b)

        await manager.enviar_a_sesion(sesion_a, {"tipo": "solo-a"})

        assert websocket_a.mensajes_recibidos == [{"tipo": "solo-a"}]
        assert websocket_b.mensajes_recibidos == []

    async def test_sesion_sin_conexiones_no_falla(self):
        manager = ConnectionManager()

        await manager.enviar_a_sesion(uuid4(), {"tipo": "nadie-escucha"})

    async def test_conexion_que_falla_al_enviar_no_interrumpe_a_las_demas(self):
        manager = ConnectionManager()
        sesion_id = uuid4()
        websocket_roto = _FakeWebSocket(falla_al_enviar=True)
        websocket_sano = _FakeWebSocket()
        await manager.conectar(sesion_id, websocket_roto)
        await manager.conectar(sesion_id, websocket_sano)

        await manager.enviar_a_sesion(sesion_id, {"tipo": "prueba"})

        assert websocket_sano.mensajes_recibidos == [{"tipo": "prueba"}]

    async def test_conexion_que_falla_al_enviar_queda_desregistrada(self):
        manager = ConnectionManager()
        sesion_id = uuid4()
        websocket_roto = _FakeWebSocket(falla_al_enviar=True)
        await manager.conectar(sesion_id, websocket_roto)

        await manager.enviar_a_sesion(sesion_id, {"tipo": "primero"})
        websocket_roto._falla_al_enviar = False
        await manager.enviar_a_sesion(sesion_id, {"tipo": "segundo"})

        assert websocket_roto.mensajes_recibidos == []


class TestDesconectar:
    def test_quita_la_conexion_del_canal(self):
        manager = ConnectionManager()
        sesion_id = uuid4()
        websocket = _FakeWebSocket()
        manager._conexiones[sesion_id] = {websocket}  # type: ignore[attr-defined]

        manager.desconectar(sesion_id, websocket)

        assert sesion_id not in manager._conexiones  # type: ignore[attr-defined]

    def test_desconectar_de_un_canal_inexistente_no_falla(self):
        manager = ConnectionManager()

        manager.desconectar(uuid4(), _FakeWebSocket())

    def test_desconectar_una_conexion_no_registrada_no_falla(self):
        manager = ConnectionManager()
        sesion_id = uuid4()
        manager._conexiones[sesion_id] = {_FakeWebSocket()}  # type: ignore[attr-defined]

        manager.desconectar(sesion_id, _FakeWebSocket())
