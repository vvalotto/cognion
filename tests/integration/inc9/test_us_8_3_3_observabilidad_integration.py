"""`/health/ready` y los logs estructurados con la aplicación real (US-8.3.3).

Requiere una base descartable (`DATABASE_URL` inline): `tests/integration/conftest.py` vacía las tablas.
Nunca apaga la base de desarrollo: la "base caída" es una dependencia en falla o una base inexistente.
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterator
from contextlib import contextmanager

import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.engine import make_url

from src.app import app
from src.settings import settings
from src.shared.frameworks.salud import comprobar_base
from tests.integration.inc8._servidor_real import ServidorReal

JWT = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c3VhcmlvIn0.firma-del-token-de-prueba"
TOKEN_INVITACION = "swBlTw_WNuuqTQICj1eE-6XB--Vr-94FOwel2qfXeUQ"
ENTORNO_BASE = {"EMAIL_MODO": "consola", "ENTORNO": "desarrollo"}


@contextmanager
def _base_caida() -> Iterator[None]:
    """Hace que el chequeo de la base falle sin tocar la base real."""

    async def caida() -> bool:
        """Caida."""
        return False

    app.dependency_overrides[comprobar_base] = caida
    try:
        yield
    finally:
        app.dependency_overrides.pop(comprobar_base, None)


def _cliente() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture
def url_de_base_inexistente() -> str:
    """La misma URL de la base, apuntada a una base que no existe."""
    return (
        make_url(settings.database_url)
        .set(database="cognion_base_que_no_existe")
        .render_as_string(hide_password=False)
    )


class TestReadinessPorHttp:
    """Los endpoints de salud por la aplicación en proceso."""

    async def test_con_la_base_disponible_responde_200(self, session):
        """Con la base disponible responde 200."""
        async with _cliente() as client:
            respuesta = await client.get("/health/ready")

        assert respuesta.status_code == 200
        assert respuesta.json() == {"status": "ok", "base_de_datos": "ok"}

    async def test_con_la_base_caida_responde_503_sin_el_motivo(self, session):
        """Con la base caida responde 503 sin el motivo."""
        with _base_caida():
            async with _cliente() as client:
                respuesta = await client.get("/health/ready")

        assert respuesta.status_code == 503
        assert respuesta.json() == {"status": "error", "base_de_datos": "no disponible"}

    async def test_no_pide_credenciales(self, session):
        """No pide credenciales."""
        async with _cliente() as client:
            sin = await client.get("/health/ready")
            con_basura = await client.get("/health/ready", headers={"Authorization": "Bearer x"})

        assert sin.status_code == 200
        assert con_basura.status_code == 200

    async def test_health_no_depende_de_la_base(self, session):
        """Health no depende de la base."""
        with _base_caida():
            async with _cliente() as client:
                respuesta = await client.get("/health")

        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert cuerpo["status"] == "ok"
        assert cuerpo["version"]  # US-10.2.1: informa la versión, sin tocar la base


class TestBaseInexistenteConServidorReal:
    """Un `uvicorn` real cuya base no existe: vivo pero sin poder atender pedidos."""

    def test_health_responde_200_y_ready_503_sin_exponer_la_clave(self, url_de_base_inexistente):
        """Health responde 200 y ready 503 sin exponer la clave."""
        servidor = ServidorReal(DATABASE_URL=url_de_base_inexistente, **ENTORNO_BASE)
        servidor.iniciar()
        try:
            vivo = httpx.get(f"{servidor.url}/health", timeout=5)
            listo = httpx.get(f"{servidor.url}/health/ready", timeout=10)
            salida = servidor.esperar_en_salida("La base de datos no está disponible")
        finally:
            servidor.detener()

        assert vivo.status_code == 200
        assert listo.status_code == 503
        assert listo.json() == {"status": "error", "base_de_datos": "no disponible"}
        assert "La base de datos no está disponible" in salida
        clave = make_url(settings.database_url).password
        if clave:
            assert clave not in salida
            assert clave not in listo.text


def _lineas_json(salida: str) -> list[dict[str, str]]:
    return [json.loads(linea) for linea in salida.splitlines() if linea.startswith("{")]


class TestFormatoDeLogsConServidorReal:
    """El formato de los logs de un `uvicorn` real."""

    def test_por_defecto_el_log_es_texto(self):
        """Por defecto el log es texto."""
        servidor = ServidorReal(**ENTORNO_BASE)
        servidor.iniciar()
        try:
            httpx.get(f"{servidor.url}/health", timeout=5)
            salida = servidor.esperar_en_salida("GET /health")
        finally:
            servidor.detener()

        assert "INFO:" in salida
        assert not any(linea.startswith("{") for linea in salida.splitlines())

    def test_con_json_cada_linea_de_la_aplicacion_y_de_uvicorn_es_json(self):
        """Con json cada linea de la aplicacion y de uvicorn es json."""
        servidor = ServidorReal(LOG_FORMAT="json", **ENTORNO_BASE)
        servidor.iniciar()
        try:
            httpx.get(f"{servidor.url}/health", timeout=5)
            salida = servidor.esperar_en_salida("GET /health")
            time.sleep(0.3)
            salida = servidor.salida()
        finally:
            servidor.detener()

        lineas = _lineas_json(salida)
        assert lineas, salida
        for datos in lineas:
            assert {"ts", "nivel", "logger", "mensaje"} <= set(datos)
        assert any(
            d["logger"] == "uvicorn.access" and "GET /health" in d["mensaje"] for d in lineas
        )
        assert any(d["logger"] == "uvicorn.error" for d in lineas)
        # Ninguna línea de log de `uvicorn` queda en texto plano.
        assert not any(linea.startswith("INFO:") for linea in salida.splitlines())

    def test_con_json_los_tokens_siguen_enmascarados(self):
        """Con json los tokens siguen enmascarados."""
        servidor = ServidorReal(LOG_FORMAT="json", **ENTORNO_BASE)
        servidor.iniciar()
        try:
            httpx.get(f"{servidor.url}/health?token={JWT}", timeout=5)
            httpx.get(f"{servidor.url}/identidad/invitaciones/{TOKEN_INVITACION}", timeout=5)
            servidor.esperar_en_salida("invitaciones")
            time.sleep(0.3)
            salida = servidor.salida()
        finally:
            servidor.detener()

        assert JWT not in salida and TOKEN_INVITACION not in salida
        mensajes = [d["mensaje"] for d in _lineas_json(salida) if d["logger"] == "uvicorn.access"]
        assert any("token=***" in m for m in mensajes)
        assert any("/invitaciones/***" in m for m in mensajes)

    def test_un_formato_invalido_impide_arrancar_y_nombra_la_variable(self):
        """Un formato invalido impide arrancar y nombra la variable."""
        servidor = ServidorReal(LOG_FORMAT="xml", **ENTORNO_BASE)

        with pytest.raises(RuntimeError) as error:
            servidor.iniciar()
        servidor.detener()

        mensaje = str(error.value).lower()
        assert "log_format" in mensaje
        assert "texto" in mensaje and "json" in mensaje
