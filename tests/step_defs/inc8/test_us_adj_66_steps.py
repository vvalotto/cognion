"""Steps BDD de US-ADJ-66 — El envío de email valida el certificado del servidor SMTP.

Sin base de datos ni internet: servidor SMTP de prueba con TLS y certificados generados al vuelo.
"""

from __future__ import annotations

import asyncio
import logging
import ssl
from collections.abc import Iterator
from typing import Any
from unittest.mock import patch
from uuid import uuid4

import pytest
from pytest_bdd import given, scenarios, then, when

from src.settings import CuentaSmtpMateria, settings
from src.shared.frameworks import smtp
from src.shared.frameworks.smtp import enviar_email
from tests.unit.inc8._servidor_smtp_tls import ServidorSmtpTls, generar_certificados

scenarios("../../features/inc8/US-ADJ-66-certificado-smtp.feature")

PASSWORD = "clave-secreta-de-prueba"
CUERPO = "Cuerpo confidencial con link de recuperación"
CERTS = generar_certificados()


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


@pytest.fixture
def ctx(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> Iterator[dict[str, Any]]:
    """Estado compartido entre steps; detiene los servidores al terminar."""
    caplog.set_level(logging.ERROR, logger="src.shared.frameworks.smtp")
    estado: dict[str, Any] = {"servidores": [], "errores": {}, "mp": monkeypatch}
    monkeypatch.setattr(settings, "email_modo", "smtp")
    monkeypatch.setattr(settings, "smtp_cuentas_por_materia", {})
    monkeypatch.setattr(settings, "smtp_host", "localhost")
    monkeypatch.setattr(settings, "smtp_from", "cognion@prueba.example")
    yield estado
    for servidor in estado["servidores"]:
        servidor.detener()


def _servidor(ctx: dict[str, Any], par) -> ServidorSmtpTls:
    servidor = ServidorSmtpTls(par=par)
    servidor.iniciar()
    ctx["servidores"].append(servidor)
    return servidor


def _confiar_en_la_autoridad_de_prueba(ctx: dict[str, Any]) -> None:
    contexto = ssl.create_default_context(cadata=CERTS.autoridad_pem.decode())
    ctx["mp"].setattr(smtp, "_contexto_tls", lambda: contexto)


def _usar_como_global(ctx: dict[str, Any], servidor: ServidorSmtpTls, user: str) -> None:
    ctx["mp"].setattr(settings, "smtp_port", servidor.puerto)
    ctx["mp"].setattr(settings, "smtp_user", user)
    ctx["mp"].setattr(settings, "smtp_password", PASSWORD if user else "")


def _enviar(ctx: dict[str, Any], clave: str, materia_id=None) -> None:
    try:
        run_async(enviar_email(materia_id, "alumno@uner.edu.ar", "Asunto", CUERPO))
        ctx["errores"][clave] = None
    except ssl.SSLCertVerificationError as error:
        ctx["errores"][clave] = error


# ----------------------------------------------------------------------- Given


@given(
    "un servidor SMTP con un certificado firmado por una autoridad de confianza y el nombre correcto"
)
def _servidor_valido(ctx):
    _confiar_en_la_autoridad_de_prueba(ctx)
    ctx["servidor"] = _servidor(ctx, CERTS.valido)
    _usar_como_global(ctx, ctx["servidor"], "cognion")


@given("un servidor SMTP con un certificado que no firma una autoridad de confianza")
def _servidor_autofirmado(ctx):
    ctx["servidor"] = _servidor(ctx, CERTS.autofirmado)
    _usar_como_global(ctx, ctx["servidor"], "cognion")


@given("un servidor SMTP con un certificado válido emitido para otro nombre")
def _servidor_otro_nombre(ctx):
    _confiar_en_la_autoridad_de_prueba(ctx)
    ctx["servidor"] = _servidor(ctx, CERTS.otro_nombre)
    _usar_como_global(ctx, ctx["servidor"], "cognion")


@given("una materia con cuenta propia cuyo servidor tiene un certificado inválido")
def _materia_invalida(ctx):
    _confiar_en_la_autoridad_de_prueba(ctx)
    ctx["materia"] = uuid4()
    ctx["servidor_materia"] = _servidor(ctx, CERTS.autofirmado)
    ctx["mp"].setattr(
        settings,
        "smtp_cuentas_por_materia",
        {
            ctx["materia"]: CuentaSmtpMateria(
                host="localhost",
                port=ctx["servidor_materia"].puerto,
                user="materia",
                password=PASSWORD,
                remitente="materia@prueba.example",
            )
        },
    )


@given("otra materia que usa la cuenta global con un certificado válido")
def _global_valida(ctx):
    ctx["servidor"] = _servidor(ctx, CERTS.valido)
    _usar_como_global(ctx, ctx["servidor"], "global")


@given("un servidor SMTP local sin usuario configurado")
def _servidor_local(ctx):
    ctx["servidor"] = _servidor(ctx, None)
    _usar_como_global(ctx, ctx["servidor"], "")


@given("el modo de envío consola")
def _modo_consola(ctx):
    ctx["mp"].setattr(settings, "email_modo", "consola")


# ------------------------------------------------------------------------ When


@when("la aplicación envía un email con una cuenta autenticada")
@when("la aplicación envía un email")
def _enviar_uno(ctx):
    if settings.email_modo == "consola":
        with patch("src.shared.frameworks.smtp.smtplib.SMTP") as conexion:
            _enviar(ctx, "unico")
        ctx["conexion"] = conexion
    else:
        _enviar(ctx, "unico")


@when("la aplicación envía un email de cada materia")
def _enviar_de_cada_materia(ctx):
    _enviar(ctx, "primera", ctx["materia"])
    _enviar(ctx, "segunda", None)


# ------------------------------------------------------------------------ Then


@then("el email sale")
def _sale(ctx):
    assert ctx["errores"]["unico"] is None
    assert "AUTH" in ctx["servidor"].comandos
    assert len(ctx["servidor"].mensajes) == 1


@then("el envío falla por certificado no verificable")
def _falla(ctx):
    assert isinstance(ctx["errores"]["unico"], ssl.SSLCertVerificationError)


@then("el servidor no recibe usuario ni contraseña")
def _sin_credenciales(ctx):
    assert "AUTH" not in ctx["servidor"].comandos


@then("el servidor no recibe el mensaje")
def _sin_mensaje(ctx):
    assert not {"MAIL", "DATA"} & set(ctx["servidor"].comandos)
    assert ctx["servidor"].mensajes == []


@then("el email de la primera materia falla por certificado no verificable")
def _primera_falla(ctx):
    assert isinstance(ctx["errores"]["primera"], ssl.SSLCertVerificationError)
    assert "AUTH" not in ctx["servidor_materia"].comandos


@then("el email de la segunda materia sale")
def _segunda_sale(ctx):
    assert ctx["errores"]["segunda"] is None
    assert len(ctx["servidor"].mensajes) == 1


@then("el email sale sin negociar TLS")
def _sin_tls(ctx):
    assert ctx["errores"]["unico"] is None
    assert "STARTTLS" not in ctx["servidor"].comandos
    assert len(ctx["servidor"].mensajes) == 1


@then("no se abre ninguna conexión")
def _sin_conexion(ctx):
    ctx["conexion"].assert_not_called()


@then("el log indica que el certificado no se pudo verificar")
def _log_indica(caplog):
    assert "No se pudo verificar el certificado" in caplog.text
    assert "localhost" in caplog.text


@then("el log no contiene la contraseña ni el cuerpo del email")
def _log_limpio(caplog):
    assert PASSWORD not in caplog.text
    assert CUERPO not in caplog.text
