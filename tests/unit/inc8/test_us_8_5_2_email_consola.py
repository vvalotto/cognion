"""`EMAIL_MODO=consola`: el email queda en el log y no se abre SMTP (US-8.5.2)."""

import logging
import uuid
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from src.identidad.entities.usuario import Docente, Usuario
from src.identidad.frameworks.adapters.canal_recuperacion_port_in_process import (
    CanalRecuperacionPortInProcess,
)
from src.identidad.use_cases.solicitar_recuperacion_password import (
    SolicitarRecuperacionPasswordUseCase,
)
from src.settings import Settings, settings
from src.shared.frameworks.smtp import enviar_email
from tests.unit.inc1._fakes import (
    FakeTokenRecuperacionPasswordRepository,
    FakeUsuarioRepository,
)

_BASE = {
    "database_url": "postgresql+asyncpg://u:p@cognion-db.flycast:5432/cognion",
    "secret_key": "x" * 40,
}
_PRODUCCION = {
    **_BASE,
    "entorno": "produccion",
    "smtp_host": "smtp.ingenieria.uner.edu.ar",
    "smtp_from": "cognion@ingenieria.uner.edu.ar",
    "frontend_url": "https://cognion.fly.dev",
    "cors_allowed_origins": "https://cognion.fly.dev",
}


async def test_modo_consola_escribe_en_el_log_y_no_usa_smtp(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Escenario 1: destinatario, asunto y cuerpo en INFO; `smtplib` no se invoca."""
    monkeypatch.setattr(settings, "email_modo", "consola")
    with (
        patch("src.shared.frameworks.smtp.smtplib.SMTP") as smtp,
        caplog.at_level(logging.INFO, logger="src.shared.frameworks.smtp"),
    ):
        await enviar_email(None, "alumno@fiuner.edu.ar", "Asunto X", "Cuerpo con link /t/abc")
    smtp.assert_not_called()
    assert "alumno@fiuner.edu.ar" in caplog.text
    assert "Asunto X" in caplog.text
    assert "Cuerpo con link /t/abc" in caplog.text


async def test_modo_smtp_conserva_el_comportamiento_actual(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Escenario 2: con `smtp` el envío abre la conexión a la cuenta resuelta."""
    monkeypatch.setattr(settings, "email_modo", "smtp")
    monkeypatch.setattr(settings, "smtp_host", "smtp.global.example")
    monkeypatch.setattr(settings, "smtp_user", "")
    with patch("src.shared.frameworks.smtp.smtplib.SMTP") as smtp:
        await enviar_email(None, "alumno@fiuner.edu.ar", "A", "B")
    smtp.assert_called_once_with("smtp.global.example", settings.smtp_port)


def test_email_modo_por_defecto_es_smtp() -> None:
    """Sin definirlo, el modo es `smtp`."""
    assert Settings(**_BASE).email_modo == "smtp"  # type: ignore[arg-type]


@pytest.mark.parametrize("entorno", ["staging", "produccion"])
def test_consola_se_rechaza_en_entornos_expuestos(entorno: str) -> None:
    """Escenario 3: el error nombra `EMAIL_MODO`."""
    with pytest.raises(ValidationError) as exc:
        Settings(**{**_PRODUCCION, "entorno": entorno, "email_modo": "consola"})  # type: ignore[arg-type]
    assert "EMAIL_MODO" in str(exc.value)


@pytest.mark.parametrize("entorno", ["desarrollo", "local"])
def test_consola_se_permite_en_desarrollo_y_local(entorno: str) -> None:
    """En local y desarrollo el modo consola arranca."""
    cfg = Settings(**{**_BASE, "entorno": entorno, "email_modo": "consola"})  # type: ignore[arg-type]
    assert cfg.email_modo == "consola"


async def test_recuperacion_en_modo_consola_deja_el_link_en_el_log(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Escenario 4: el link con token queda en el log y el caso de uso responde igual."""
    monkeypatch.setattr(settings, "email_modo", "consola")
    usuario_repo = FakeUsuarioRepository()
    token_repo = FakeTokenRecuperacionPasswordRepository()
    usuario_id = uuid.uuid4()
    await usuario_repo.guardar(
        Usuario(
            id=usuario_id,
            nombre="Docente",
            email="docente@fiuner.edu.ar",
            password_hash="hash",
            perfil=Docente(id=usuario_id),
        )
    )
    use_case = SolicitarRecuperacionPasswordUseCase(
        usuario_repo, token_repo, CanalRecuperacionPortInProcess()
    )
    with (
        patch("src.shared.frameworks.smtp.smtplib.SMTP") as smtp,
        caplog.at_level(logging.INFO, logger="src.shared.frameworks.smtp"),
    ):
        resultado = await use_case.execute("docente@fiuner.edu.ar")
        inexistente = await use_case.execute("nadie@fiuner.edu.ar")
    token = next(iter(token_repo.tokens.values())).token
    smtp.assert_not_called()
    assert f"/recuperar-password/{token}" in caplog.text
    assert resultado == inexistente  # indistinguible (INV-ID-17)
