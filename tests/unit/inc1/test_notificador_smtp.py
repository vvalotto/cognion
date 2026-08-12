from unittest.mock import MagicMock, patch

from src.identidad.frameworks.smtp.notificador_smtp import SmtpNotificador


class TestSmtpNotificador:
    async def test_enviar_invitacion_conecta_y_envia_mensaje(self):
        smtp_mock = MagicMock()
        smtp_mock.__enter__.return_value = smtp_mock

        with patch(
            "src.identidad.frameworks.smtp.notificador_smtp.smtplib.SMTP",
            return_value=smtp_mock,
        ) as smtp_class:
            notificador = SmtpNotificador()
            await notificador.enviar_invitacion("estudiante@fiuner.edu.ar", "token-123")

        smtp_class.assert_called_once()
        smtp_mock.send_message.assert_called_once()
        mensaje_enviado = smtp_mock.send_message.call_args[0][0]
        assert mensaje_enviado["To"] == "estudiante@fiuner.edu.ar"
        assert "token-123" in mensaje_enviado.get_content()

    async def test_hace_login_solo_si_hay_usuario_configurado(self):
        smtp_mock = MagicMock()
        smtp_mock.__enter__.return_value = smtp_mock

        with patch(
            "src.identidad.frameworks.smtp.notificador_smtp.smtplib.SMTP",
            return_value=smtp_mock,
        ):
            notificador = SmtpNotificador()
            await notificador.enviar_invitacion("estudiante@fiuner.edu.ar", "token-123")

        smtp_mock.login.assert_not_called()
