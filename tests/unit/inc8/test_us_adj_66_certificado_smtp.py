"""El envío de email valida el certificado del servidor SMTP (US-ADJ-66, ADR-023)."""

from __future__ import annotations

import logging
import ssl
from collections.abc import Iterator
from unittest.mock import patch
from uuid import uuid4

import pytest

from src.settings import CuentaSmtpMateria, settings
from src.shared.frameworks import smtp
from src.shared.frameworks.smtp import enviar_email
from tests.unit.inc8._servidor_smtp_tls import (
    Certificados,
    ServidorSmtpTls,
    generar_certificados,
)

PASSWORD = "clave-secreta-de-prueba"
CUERPO = "Cuerpo confidencial con link de recuperación"


@pytest.fixture(scope="module")
def certificados() -> Certificados:
    """Autoridad de prueba y certificados de servidor (se generan una sola vez)."""
    return generar_certificados()


@pytest.fixture
def servidores() -> Iterator[list[ServidorSmtpTls]]:
    """Lista de servidores que se detienen al terminar la prueba."""
    creados: list[ServidorSmtpTls] = []
    yield creados
    for servidor in creados:
        servidor.detener()


def _levantar(servidores: list[ServidorSmtpTls], par: object) -> ServidorSmtpTls:
    servidor = ServidorSmtpTls(par=par)  # type: ignore[arg-type]
    servidor.iniciar()
    servidores.append(servidor)
    return servidor


def _confiar_en(monkeypatch: pytest.MonkeyPatch, autoridad_pem: bytes) -> None:
    """Hace que la validación acepte solo la autoridad de prueba (sin internet ni `certifi`)."""
    contexto = ssl.create_default_context(cadata=autoridad_pem.decode())
    monkeypatch.setattr(smtp, "_contexto_tls", lambda: contexto)


def _cuenta_global(monkeypatch: pytest.MonkeyPatch, servidor: ServidorSmtpTls, user: str) -> None:
    monkeypatch.setattr(settings, "email_modo", "smtp")
    monkeypatch.setattr(settings, "smtp_cuentas_por_materia", {})
    monkeypatch.setattr(settings, "smtp_host", "localhost")
    monkeypatch.setattr(settings, "smtp_port", servidor.puerto)
    monkeypatch.setattr(settings, "smtp_user", user)
    monkeypatch.setattr(settings, "smtp_password", PASSWORD if user else "")
    monkeypatch.setattr(settings, "smtp_from", "cognion@prueba.example")


async def test_certificado_valido_el_email_sale(
    monkeypatch: pytest.MonkeyPatch,
    certificados: Certificados,
    servidores: list[ServidorSmtpTls],
) -> None:
    """Escenario 1: autoridad de confianza y nombre correcto → llegan AUTH y el mensaje."""
    servidor = _levantar(servidores, certificados.valido)
    _confiar_en(monkeypatch, certificados.autoridad_pem)
    _cuenta_global(monkeypatch, servidor, user="cognion")

    await enviar_email(None, "alumno@uner.edu.ar", "Asunto", CUERPO)

    assert "AUTH" in servidor.comandos
    assert len(servidor.mensajes) == 1
    assert CUERPO in servidor.mensajes[0]


async def test_certificado_autofirmado_falla_sin_enviar_secretos(
    monkeypatch: pytest.MonkeyPatch,
    certificados: Certificados,
    servidores: list[ServidorSmtpTls],
) -> None:
    """Escenario 2: con el bundle real de `certifi`, un autofirmado no es verificable."""
    servidor = _levantar(servidores, certificados.autofirmado)
    _cuenta_global(monkeypatch, servidor, user="cognion")

    with pytest.raises(ssl.SSLCertVerificationError):
        await enviar_email(None, "alumno@uner.edu.ar", "Asunto", CUERPO)

    assert not {"AUTH", "MAIL", "DATA"} & set(servidor.comandos)
    assert servidor.mensajes == []


async def test_nombre_distinto_falla_sin_enviar_secretos(
    monkeypatch: pytest.MonkeyPatch,
    certificados: Certificados,
    servidores: list[ServidorSmtpTls],
) -> None:
    """Escenario 3: certificado de una autoridad confiable, pero emitido para otro nombre."""
    servidor = _levantar(servidores, certificados.otro_nombre)
    _confiar_en(monkeypatch, certificados.autoridad_pem)
    _cuenta_global(monkeypatch, servidor, user="cognion")

    with pytest.raises(ssl.SSLCertVerificationError):
        await enviar_email(None, "alumno@uner.edu.ar", "Asunto", CUERPO)

    assert "AUTH" not in servidor.comandos
    assert servidor.mensajes == []


async def test_una_materia_con_certificado_invalido_no_afecta_a_las_demas(
    monkeypatch: pytest.MonkeyPatch,
    certificados: Certificados,
    servidores: list[ServidorSmtpTls],
) -> None:
    """Escenario 4: cada cuenta se valida por separado."""
    materia = uuid4()
    invalido = _levantar(servidores, certificados.autofirmado)
    valido = _levantar(servidores, certificados.valido)
    _confiar_en(monkeypatch, certificados.autoridad_pem)
    _cuenta_global(monkeypatch, valido, user="global")
    monkeypatch.setattr(
        settings,
        "smtp_cuentas_por_materia",
        {
            materia: CuentaSmtpMateria(
                host="localhost",
                port=invalido.puerto,
                user="materia",
                password=PASSWORD,
                remitente="materia@prueba.example",
            )
        },
    )

    with pytest.raises(ssl.SSLCertVerificationError):
        await enviar_email(materia, "alumno@uner.edu.ar", "Asunto", CUERPO)
    await enviar_email(None, "alumno@uner.edu.ar", "Asunto", CUERPO)

    assert "AUTH" not in invalido.comandos
    assert len(valido.mensajes) == 1


async def test_servidor_local_sin_usuario_no_negocia_tls(
    monkeypatch: pytest.MonkeyPatch, servidores: list[ServidorSmtpTls]
) -> None:
    """Escenario 5: sin usuario no hay STARTTLS ni validación (servidor local de pruebas)."""
    servidor = _levantar(servidores, None)
    _cuenta_global(monkeypatch, servidor, user="")

    await enviar_email(None, "alumno@uner.edu.ar", "Asunto", CUERPO)

    assert "STARTTLS" not in servidor.comandos
    assert len(servidor.mensajes) == 1


async def test_modo_consola_no_abre_conexion(monkeypatch: pytest.MonkeyPatch) -> None:
    """Escenario 6."""
    monkeypatch.setattr(settings, "email_modo", "consola")
    with patch("src.shared.frameworks.smtp.smtplib.SMTP") as conexion:
        await enviar_email(None, "alumno@uner.edu.ar", "Asunto", CUERPO)
    conexion.assert_not_called()


async def test_el_error_se_registra_sin_exponer_secretos(
    monkeypatch: pytest.MonkeyPatch,
    certificados: Certificados,
    servidores: list[ServidorSmtpTls],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Escenario 7: el log nombra el servidor y el motivo, nunca la contraseña ni el cuerpo."""
    servidor = _levantar(servidores, certificados.autofirmado)
    _cuenta_global(monkeypatch, servidor, user="cognion")

    with caplog.at_level(logging.ERROR, logger="src.shared.frameworks.smtp"):
        with pytest.raises(ssl.SSLCertVerificationError):
            await enviar_email(None, "alumno@uner.edu.ar", "Asunto", CUERPO)

    texto = caplog.text
    assert "No se pudo verificar el certificado" in texto
    assert "localhost" in texto
    assert PASSWORD not in texto
    assert CUERPO not in texto


def test_el_contexto_exige_certificado_y_nombre() -> None:
    """El contexto real nunca queda en modo permisivo."""
    contexto = smtp._contexto_tls()
    assert contexto.verify_mode == ssl.CERT_REQUIRED
    assert contexto.check_hostname is True
