"""`US-12.2.2`: el `detail` de los errores con cuerpo estructurado es el que los routers armaban a mano."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.identidad.entities.errors import (
    CredencialesInvalidas,
    CuentaBloqueadaTemporalmenteError,
    CuentaDeshabilitadaError,
    PasswordActualIncorrecta,
    UltimoAdministradorOperativoError,
)
from src.shared.entities.errors import JWTExpirado, JWTInvalido, ReglaViolada


def test_un_error_comun_responde_su_texto() -> None:
    assert ReglaViolada("texto").detalle() == "texto"


def test_cuenta_deshabilitada_responde_su_codigo() -> None:
    exc = CuentaDeshabilitadaError(uuid4())
    assert exc.detalle() == {"codigo": "cuenta_deshabilitada", "mensaje": str(exc)}


def test_ultimo_administrador_responde_su_codigo() -> None:
    exc = UltimoAdministradorOperativoError(uuid4())
    assert exc.detalle() == {"codigo": "ultimo_administrador_operativo", "mensaje": str(exc)}


def test_credenciales_invalidas_responde_texto_sin_aviso() -> None:
    exc = CredencialesInvalidas()
    assert exc.detalle() == "Email o contraseña inválidos."


def test_credenciales_invalidas_avisa_los_intentos_restantes() -> None:
    exc = CredencialesInvalidas()
    exc.intentos_restantes = 1
    assert exc.detalle() == {"mensaje": str(exc), "intentos_restantes": 1}


def test_password_actual_incorrecta_informa_los_intentos_restantes() -> None:
    exc = PasswordActualIncorrecta()
    exc.intentos_restantes = 2
    assert exc.detalle() == {"mensaje": str(exc), "intentos_restantes": 2}


def test_password_actual_incorrecta_informa_que_bloqueo_la_cuenta() -> None:
    exc = PasswordActualIncorrecta()
    exc.evento_cuenta_bloqueada = object()  # type: ignore[assignment]
    assert exc.detalle() == {"mensaje": str(exc), "bloqueada": True}


def test_bloqueo_temporal_informa_los_segundos_para_reintentar() -> None:
    hasta = datetime.now(UTC) + timedelta(minutes=10)
    detalle = CuentaBloqueadaTemporalmenteError(uuid4(), hasta).detalle()
    assert detalle["codigo"] == "cuenta_bloqueada_temporal"
    assert 590 <= detalle["reintentar_en_segundos"] <= 601


def test_los_errores_de_jwt_tienen_su_mensaje() -> None:
    assert JWTInvalido().detalle() == "Token inválido."
    assert JWTExpirado().detalle() == "Token expirado."
