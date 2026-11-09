"""Steps BDD de US-8.3.3: logs estructurados y healthcheck de readiness."""

from __future__ import annotations

import io
import json
import logging
import os
import stat
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import httpx
import pytest
from pytest_bdd import given, scenarios, then, when
from sqlalchemy.engine import make_url

from src.settings import settings
from src.shared.frameworks.logging_config import FormateadorJson
from tests.integration.inc8._servidor_real import ServidorReal

scenarios("../../features/inc9/US-8.3.3-observabilidad.feature")

RAIZ = Path(__file__).resolve().parents[3]
ENTORNO_BASE = {"EMAIL_MODO": "consola", "ENTORNO": "desarrollo"}
JWT = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c3VhcmlvIn0.firma-del-token-de-prueba"
TOKEN_INVITACION = "swBlTw_WNuuqTQICj1eE-6XB--Vr-94FOwel2qfXeUQ"


@pytest.fixture
def context() -> Iterator[dict[str, Any]]:
    """Estado compartido entre los steps; detiene el servidor real al terminar el escenario."""
    estado: dict[str, Any] = {}
    yield estado
    servidor = estado.get("servidor")
    if servidor is not None:
        servidor.detener()


def _url_de_base_inexistente() -> str:
    return (
        make_url(settings.database_url)
        .set(database="cognion_base_que_no_existe")
        .render_as_string(hide_password=False)
    )


def _levantar(context: dict[str, Any], **entorno: str) -> ServidorReal:
    servidor = ServidorReal(**{**ENTORNO_BASE, **entorno})
    context["servidor"] = servidor
    servidor.iniciar()
    return servidor


def _lineas_json(salida: str) -> list[dict[str, str]]:
    return [json.loads(linea) for linea in salida.splitlines() if linea.startswith("{")]


@given("la aplicación con la base de datos caída")
def app_con_base_caida(context):
    """Levanta un `uvicorn` real cuya base de datos no existe."""
    _levantar(context, DATABASE_URL=_url_de_base_inexistente())


@given("la aplicación con la base de datos disponible")
def app_con_base_disponible(context):
    """Levanta un `uvicorn` real contra la base descartable."""
    _levantar(context)


@given("la aplicación arrancada sin LOG_FORMAT")
def app_sin_log_format(context):
    """Levanta un `uvicorn` real sin definir `LOG_FORMAT`."""
    os.environ.pop("LOG_FORMAT", None)
    _levantar(context)


@given("la aplicación arrancada con LOG_FORMAT=json")
def app_con_json(context):
    """Levanta un `uvicorn` real con logs en JSON."""
    _levantar(context, LOG_FORMAT="json")


@given("una configuración con LOG_FORMAT=xml")
def config_invalida(context):
    """Prepara la configuración inválida; el arranque se intenta en el `When`."""
    context["entorno_invalido"] = {"LOG_FORMAT": "xml"}


@given("la salida de los dos healthchecks de una aplicación con la base caída")
def salida_de_dos_healthchecks(context, tmp_path):
    """Arma un `curl` simulado que responde 200 a `/api/health` y 503 a `/api/health/ready`."""
    falso = tmp_path / "curl"
    falso.write_text(
        "#!/usr/bin/env bash\n"
        'for a in "$@"; do url="$a"; done\n'
        'case "$url" in\n'
        '  */api/health/ready) printf \'%s\\n%s\' \'{"status":"error","base_de_datos":"no disponible"}\' 503 ;;\n'
        "  */api/health) printf '%s\\n%s' '{\"status\":\"ok\"}' 200 ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    falso.chmod(falso.stat().st_mode | stat.S_IEXEC)
    context["curl_falso"] = tmp_path


@when("se consulta /health")
def consulta_health(context):
    """Consulta `/health` del servidor real."""
    context["response"] = httpx.get(f"{context['servidor'].url}/health", timeout=10)


@when("se consulta /health/ready")
def consulta_ready(context):
    """Consulta `/health/ready` del servidor real."""
    context["response"] = httpx.get(f"{context['servidor'].url}/health/ready", timeout=10)


@when("se consulta /health/ready sin Authorization")
def consulta_ready_sin_auth(context):
    """Consulta `/health/ready` sin ningún encabezado de autenticación."""
    context["response"] = httpx.get(
        f"{context['servidor'].url}/health/ready", headers={}, timeout=10
    )


@when("la aplicación escribe un mensaje de log")
def escribe_log(context):
    """Provoca una línea de log del servidor real (el acceso a `/health`)."""
    httpx.get(f"{context['servidor'].url}/health", timeout=5)
    context["salida"] = context["servidor"].esperar_en_salida("GET /health")


@when("la aplicación y uvicorn escriben mensajes de log")
def escribe_logs_json(context):
    """Provoca líneas de la aplicación (arranque) y de `uvicorn` (acceso)."""
    escribe_log(context)
    time.sleep(0.3)
    context["salida"] = context["servidor"].salida()


@when("se registra un error con su excepción")
def registra_excepcion(context):
    """Registra una excepción con el formateador JSON y captura la salida."""
    flujo = io.StringIO()
    handler = logging.StreamHandler(flujo)
    handler.setFormatter(FormateadorJson())
    logger = logging.getLogger("src.prueba_bdd_8_3_3")
    logger.addHandler(handler)
    logger.propagate = False
    try:
        try:
            raise ValueError("falló algo")
        except ValueError:
            logger.exception("Se rompió")
    finally:
        logger.removeHandler(handler)
    context["salida"] = flujo.getvalue()


@when("llega un pedido con un token en la query y otro a la ruta de una invitación")
def pedidos_con_tokens(context):
    """Envía un pedido con un JWT en la query y otro a la ruta de una invitación."""
    url = context["servidor"].url
    httpx.get(f"{url}/health?token={JWT}", timeout=5)
    httpx.get(f"{url}/identidad/invitaciones/{TOKEN_INVITACION}", timeout=5)
    context["servidor"].esperar_en_salida("invitaciones")
    time.sleep(0.3)
    context["salida"] = context["servidor"].salida()


@when("se intenta arrancar la aplicación")
def intenta_arrancar(context):
    """Intenta arrancar el servidor real con la configuración inválida."""
    servidor = ServidorReal(**{**ENTORNO_BASE, **context["entorno_invalido"]})
    context["servidor"] = servidor
    with pytest.raises(RuntimeError) as error:
        servidor.iniciar()
    context["error_de_arranque"] = str(error.value)


@when("cognion.sh estado arma el resumen")
def arma_resumen(context):
    """Ejecuta `mostrar_salud` (la parte de `cognion.sh estado` que arma el resumen) con el `curl` simulado."""
    entorno = {**os.environ, "PATH": f"{context['curl_falso']}:{os.environ['PATH']}"}
    resultado = subprocess.run(  # noqa: S603
        [
            "bash",
            "-c",
            f"source {RAIZ}/deploy/gcp/salud.sh && mostrar_salud https://ejemplo.duckdns.org",
        ],  # noqa: S607
        env=entorno,
        capture_output=True,
        text=True,
        check=False,
    )
    context["resumen"] = resultado


@then("responde 200 con status ok")
def responde_200_ok(context):
    """La respuesta es 200 con `status: ok`."""
    assert context["response"].status_code == 200
    assert context["response"].json()["status"] == "ok"


@then("responde 200 con status ok y base_de_datos ok")
def responde_200_ready(context):
    """La respuesta es 200 con la base `ok`."""
    assert context["response"].status_code == 200
    assert context["response"].json() == {"status": "ok", "base_de_datos": "ok"}


@then("responde 200")
def responde_200(context):
    """La respuesta es 200."""
    assert context["response"].status_code == 200


@then("responde 503 con status error y base_de_datos no disponible")
def responde_503(context):
    """La respuesta es 503 con la base `no disponible`."""
    assert context["response"].status_code == 503
    assert context["response"].json() == {"status": "error", "base_de_datos": "no disponible"}


@then("el cuerpo no incluye el motivo, la dirección ni la contraseña de la base")
def cuerpo_sin_detalles(context):
    """El cuerpo del 503 no trae el motivo, el host ni la clave."""
    cuerpo = context["response"].text.lower()
    url = make_url(settings.database_url)
    for dato in (url.password, url.host, "cognion_base_que_no_existe", "postgres", "asyncpg"):
        if dato:
            assert str(dato).lower() not in cuerpo


@then("el error queda en el log sin la contraseña")
def error_en_el_log(context):
    """El log tiene el error de la base y no la clave."""
    salida = context["servidor"].esperar_en_salida("La base de datos no está disponible")
    assert "La base de datos no está disponible" in salida
    clave = make_url(settings.database_url).password
    if clave:
        assert clave not in salida


@then("la línea tiene el formato de texto de siempre")
def formato_texto(context):
    """Las líneas son de texto (`INFO:  ...`) y ninguna es JSON."""
    lineas = context["salida"].splitlines()
    assert any(linea.startswith("INFO:") for linea in lineas)
    assert not any(linea.startswith("{") for linea in lineas)


@then("cada línea es un JSON válido con ts, nivel, logger y mensaje")
def lineas_json(context):
    """Todas las líneas de log son JSON con los cuatro campos, y ninguna quedó en texto."""
    salida = context["salida"]
    datos = _lineas_json(salida)
    assert datos, salida
    for registro in datos:
        assert {"ts", "nivel", "logger", "mensaje"} <= set(registro)
    assert any(r["logger"] == "uvicorn.access" for r in datos)
    assert any(r["logger"] == "uvicorn.error" for r in datos)
    assert not any(linea.startswith("INFO:") for linea in salida.splitlines())


@then("sale una sola línea JSON con el campo excepcion")
def una_linea_con_excepcion(context):
    """El error con excepción salió en una sola línea JSON con `excepcion`."""
    lineas = context["salida"].strip().splitlines()
    assert len(lineas) == 1
    assert "ValueError: falló algo" in json.loads(lineas[0])["excepcion"]


@then("ninguna línea del log contiene el token y aparece ***")
def tokens_enmascarados(context):
    """Los tokens no aparecen y el log tiene `***` en su lugar."""
    salida = context["salida"]
    assert JWT not in salida and TOKEN_INVITACION not in salida
    mensajes = [d["mensaje"] for d in _lineas_json(salida) if d["logger"] == "uvicorn.access"]
    assert any("token=***" in m for m in mensajes)
    assert any("/invitaciones/***" in m for m in mensajes)


@then("el arranque falla y el mensaje nombra LOG_FORMAT y los valores texto y json")
def arranque_falla(context):
    """El arranque falló y el mensaje nombra la variable y los valores válidos."""
    mensaje = context["error_de_arranque"].lower()
    assert "log_format" in mensaje
    assert "texto" in mensaje and "json" in mensaje


@then("muestra la respuesta de /api/health y la de /api/health/ready indicando el 503")
def resumen_con_503(context):
    """El resumen trae las dos respuestas, marca el 503 y no oculta el 200 de `/api/health`."""
    salida = context["resumen"].stdout
    assert context["resumen"].returncode == 0
    assert "/api/health " in salida and "200" in salida and '{"status":"ok"}' in salida
    assert "/api/health/ready" in salida and "503" in salida and "no disponible" in salida
    assert "no está lista para atender pedidos" in salida
