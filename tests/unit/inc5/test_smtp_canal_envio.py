"""Tests unitarios de `SmtpCanalEnvio` (US-5.1.1).

Mismo patrón de mocking que `tests/unit/inc1/test_notificador_smtp.py` (`ADR-012`) — los dos
adaptadores comparten técnica (`smtplib` + `asyncio.to_thread`).
"""

from unittest.mock import MagicMock, patch

from src.notificaciones.frameworks.adapters.smtp_canal_envio import SmtpCanalEnvio
from src.settings import settings


class TestSmtpCanalEnvio:
    async def test_enviar_conecta_y_envia_mensaje(self):
        smtp_mock = MagicMock()
        smtp_mock.__enter__.return_value = smtp_mock

        with patch(
            "src.notificaciones.frameworks.adapters.smtp_canal_envio.smtplib.SMTP",
            return_value=smtp_mock,
        ) as smtp_class:
            canal = SmtpCanalEnvio()
            await canal.enviar("estudiante@fiuner.edu.ar", "Asunto de prueba", "Cuerpo de prueba")

        smtp_class.assert_called_once()
        smtp_mock.send_message.assert_called_once()
        mensaje_enviado = smtp_mock.send_message.call_args[0][0]
        assert mensaje_enviado["To"] == "estudiante@fiuner.edu.ar"
        assert mensaje_enviado["Subject"] == "Asunto de prueba"
        assert "Cuerpo de prueba" in mensaje_enviado.get_content()

    async def test_hace_login_solo_si_hay_usuario_configurado(self):
        smtp_mock = MagicMock()
        smtp_mock.__enter__.return_value = smtp_mock

        with patch(
            "src.notificaciones.frameworks.adapters.smtp_canal_envio.smtplib.SMTP",
            return_value=smtp_mock,
        ):
            canal = SmtpCanalEnvio()
            await canal.enviar("estudiante@fiuner.edu.ar", "Asunto", "Cuerpo")

        smtp_mock.login.assert_not_called()

    async def test_hace_starttls_y_login_si_hay_usuario_configurado(self, monkeypatch):
        monkeypatch.setattr(settings, "smtp_user", "usuario-smtp")
        monkeypatch.setattr(settings, "smtp_password", "clave-smtp")
        smtp_mock = MagicMock()
        smtp_mock.__enter__.return_value = smtp_mock

        with patch(
            "src.notificaciones.frameworks.adapters.smtp_canal_envio.smtplib.SMTP",
            return_value=smtp_mock,
        ):
            canal = SmtpCanalEnvio()
            await canal.enviar("estudiante@fiuner.edu.ar", "Asunto", "Cuerpo")

        smtp_mock.starttls.assert_called_once()
        smtp_mock.login.assert_called_once_with("usuario-smtp", "clave-smtp")
