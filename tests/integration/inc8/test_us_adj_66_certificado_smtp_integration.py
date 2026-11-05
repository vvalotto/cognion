"""Los dos adaptadores reales validan el certificado SMTP de punta a punta (US-ADJ-66)."""

from __future__ import annotations

import ssl
from collections.abc import Iterator

import pytest

from src.identidad.frameworks.smtp.notificador_smtp import SmtpNotificador
from src.notificaciones.frameworks.adapters.smtp_canal_envio import SmtpCanalEnvio
from src.settings import settings
from src.shared.frameworks import smtp
from tests.unit.inc8._servidor_smtp_tls import (
    Certificados,
    ServidorSmtpTls,
    generar_certificados,
)


@pytest.fixture(scope="module")
def certificados() -> Certificados:
    """Autoridad de prueba y certificados de servidor."""
    return generar_certificados()


@pytest.fixture
def servidor(
    monkeypatch: pytest.MonkeyPatch, certificados: Certificados, request: pytest.FixtureRequest
) -> Iterator[ServidorSmtpTls]:
    """Servidor con el certificado indicado en `request.param`, configurado como cuenta global."""
    par = getattr(certificados, request.param)
    srv = ServidorSmtpTls(par=par)
    srv.iniciar()
    contexto = ssl.create_default_context(cadata=certificados.autoridad_pem.decode())
    monkeypatch.setattr(smtp, "_contexto_tls", lambda: contexto)
    monkeypatch.setattr(settings, "email_modo", "smtp")
    monkeypatch.setattr(settings, "smtp_cuentas_por_materia", {})
    monkeypatch.setattr(settings, "smtp_host", "localhost")
    monkeypatch.setattr(settings, "smtp_port", srv.puerto)
    monkeypatch.setattr(settings, "smtp_user", "cognion")
    monkeypatch.setattr(settings, "smtp_password", "clave-de-prueba")
    monkeypatch.setattr(settings, "smtp_from", "cognion@prueba.example")
    yield srv
    srv.detener()


@pytest.mark.parametrize("servidor", ["valido"], indirect=True)
async def test_canal_de_notificaciones_envia_con_certificado_valido(
    servidor: ServidorSmtpTls,
) -> None:
    """`SmtpCanalEnvio` llega hasta el servidor con TLS validado."""
    await SmtpCanalEnvio().enviar("alumno@uner.edu.ar", "Apertura", "Cuerpo")
    assert "AUTH" in servidor.comandos
    assert len(servidor.mensajes) == 1


@pytest.mark.parametrize("servidor", ["otro_nombre"], indirect=True)
async def test_canal_de_notificaciones_rechaza_certificado_de_otro_nombre(
    servidor: ServidorSmtpTls,
) -> None:
    """Con un certificado de otro nombre, el adaptador falla y el servidor no ve credenciales."""
    with pytest.raises(ssl.SSLCertVerificationError):
        await SmtpCanalEnvio().enviar("alumno@uner.edu.ar", "Apertura", "Cuerpo")
    assert "AUTH" not in servidor.comandos
    assert servidor.mensajes == []


@pytest.mark.parametrize("servidor", ["autofirmado"], indirect=True)
async def test_notificador_de_identidad_rechaza_certificado_autofirmado(
    servidor: ServidorSmtpTls,
) -> None:
    """El adaptador de Identidad (invitación) comparte la misma validación."""
    with pytest.raises(ssl.SSLCertVerificationError):
        await SmtpNotificador().enviar_invitacion("alumno@uner.edu.ar", "token-secreto")
    assert "AUTH" not in servidor.comandos
