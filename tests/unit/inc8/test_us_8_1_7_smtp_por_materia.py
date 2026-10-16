"""Cuenta SMTP resuelta por materia con fallback global (US-8.1.7, ADR-023)."""

import json
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from src.identidad.entities.comision import Comision
from src.identidad.use_cases.generar_invitacion import GenerarInvitacionUseCase
from src.settings import CuentaSmtpMateria, Settings, settings
from src.shared.frameworks.smtp import enviar_email, resolver_cuenta_smtp
from tests.unit.inc1._fakes import (
    FakeComisionRepository,
    FakeInvitacionRepository,
    FakeNotificador,
)

MATERIA_CON_CUENTA = uuid4()
MATERIA_SIN_CUENTA = uuid4()
CUENTA = CuentaSmtpMateria(
    host="smtp.gestion.uner.edu.ar",
    port=587,
    user="gestion",
    password="clave-secreta-de-prueba",
    remitente="gestiondeproyectos@ingenieria.uner.edu.ar",
)
_VALIDOS = {
    "database_url": "postgresql+asyncpg://u:p@cognion-db.flycast:5432/cognion",
    "secret_key": "x" * 40,
    "smtp_host": "smtp.ingenieria.uner.edu.ar",
    "smtp_from": "cognion@ingenieria.uner.edu.ar",
    "frontend_url": "https://cognion.fly.dev",
    "cors_allowed_origins": "https://cognion.fly.dev",
}


@pytest.fixture(autouse=True)
def _cuentas_configuradas(monkeypatch: pytest.MonkeyPatch) -> None:
    """Una materia con cuenta propia y la cuenta global apuntando a otro servidor."""
    monkeypatch.setattr(settings, "smtp_cuentas_por_materia", {MATERIA_CON_CUENTA: CUENTA})
    monkeypatch.setattr(settings, "smtp_host", "smtp.global.example")
    monkeypatch.setattr(settings, "smtp_port", 25)
    monkeypatch.setattr(settings, "smtp_user", "")
    monkeypatch.setattr(settings, "smtp_from", "global@cognion.example")


def test_materia_con_cuenta_propia_usa_esa_cuenta() -> None:
    """Escenario 1: servidor, puerto, credenciales y remitente son los de la materia."""
    cuenta = resolver_cuenta_smtp(MATERIA_CON_CUENTA)
    assert (cuenta.host, cuenta.port, cuenta.user) == ("smtp.gestion.uner.edu.ar", 587, "gestion")
    assert cuenta.remitente == "gestiondeproyectos@ingenieria.uner.edu.ar"


@pytest.mark.parametrize("materia_id", [MATERIA_SIN_CUENTA, None])
def test_sin_cuenta_propia_o_sin_materia_usa_la_global(materia_id: UUID | None) -> None:
    """Escenarios 2 y 3: materia sin cuenta, o mensaje sin materia (recuperación)."""
    cuenta = resolver_cuenta_smtp(materia_id)
    assert cuenta.host == "smtp.global.example"
    assert cuenta.remitente == "global@cognion.example"


async def test_el_email_sale_con_el_remitente_y_servidor_de_la_materia() -> None:
    """El envío real arma el mensaje con la cuenta resuelta, con login por tener usuario."""
    with patch("src.shared.frameworks.smtp.smtplib.SMTP") as smtp:
        await enviar_email(MATERIA_CON_CUENTA, "alumno@uner.edu.ar", "Asunto", "Cuerpo")
    smtp.assert_called_once_with("smtp.gestion.uner.edu.ar", 587)
    servidor = smtp.return_value.__enter__.return_value
    servidor.login.assert_called_once_with("gestion", "clave-secreta-de-prueba")
    mensaje = servidor.send_message.call_args.args[0]
    assert mensaje["From"] == "gestiondeproyectos@ingenieria.uner.edu.ar"
    assert mensaje["To"] == "alumno@uner.edu.ar"


async def test_sin_materia_el_email_sale_por_la_cuenta_global() -> None:
    """Escenario 3 de punta a punta: la cuenta global, sin login si no hay usuario."""
    with patch("src.shared.frameworks.smtp.smtplib.SMTP") as smtp:
        await enviar_email(None, "alumno@uner.edu.ar", "Asunto", "Cuerpo")
    smtp.assert_called_once_with("smtp.global.example", 25)
    assert not smtp.return_value.__enter__.return_value.login.called


def test_las_cuentas_se_leen_desde_json_en_el_entorno(monkeypatch: pytest.MonkeyPatch) -> None:
    """La variable `SMTP_CUENTAS_POR_MATERIA` es un JSON con clave `materia_id`."""
    materia = uuid4()
    monkeypatch.setenv(
        "SMTP_CUENTAS_POR_MATERIA",
        json.dumps({str(materia): {"host": "smtp.x.edu.ar", "remitente": "x@x.edu.ar"}}),
    )
    cfg = Settings(database_url="postgresql://x", secret_key="t")
    assert cfg.smtp_cuentas_por_materia[materia].host == "smtp.x.edu.ar"
    assert cfg.smtp_cuentas_por_materia[materia].port == 25


def test_clave_que_no_es_uuid_es_error_de_configuracion() -> None:
    """Escenario 4."""
    with pytest.raises(ValidationError):
        Settings(
            database_url="postgresql://x",
            secret_key="t",
            smtp_cuentas_por_materia={"no-es-uuid": CUENTA},  # type: ignore[dict-item]
        )


@pytest.mark.parametrize(
    "cuenta",
    [
        CuentaSmtpMateria(host="localhost", remitente="m@uner.edu.ar", password="no-filtrar-esto"),
        CuentaSmtpMateria(
            host="smtp.uner.edu.ar", remitente="m@cognion.local", password="no-filtrar-esto"
        ),
    ],
)
def test_en_produccion_una_cuenta_de_ejemplo_se_rechaza_sin_filtrar_la_clave(
    cuenta: CuentaSmtpMateria,
) -> None:
    """Escenario 5: el error nombra la variable y nunca incluye la contraseña."""
    with pytest.raises(ValidationError) as info:
        Settings(
            **_VALIDOS,  # type: ignore[arg-type]
            entorno="produccion",
            smtp_cuentas_por_materia={uuid4(): cuenta},
        )
    texto = str(info.value)
    assert "SMTP_CUENTAS_POR_MATERIA" in texto
    assert "no-filtrar-esto" not in texto


async def test_la_invitacion_se_envia_con_la_materia_de_la_comision() -> None:
    """Escenario 6: `GenerarInvitacion` pasa `comision.materia_id` al notificador."""
    comision_repo, invitacion_repo, notificador = (
        FakeComisionRepository(),
        FakeInvitacionRepository(),
        FakeNotificador(),
    )
    docente_id = uuid4()
    comision = Comision.crear(MATERIA_CON_CUENTA, "lu 10-12", uuid4())
    comision.asignar_docente(docente_id)
    await comision_repo.guardar(comision)

    await GenerarInvitacionUseCase(comision_repo, invitacion_repo, notificador).execute(
        comision.id, docente_id, "alumno@uner.edu.ar", solicitante_id=docente_id
    )

    assert notificador.materias == [MATERIA_CON_CUENTA]
