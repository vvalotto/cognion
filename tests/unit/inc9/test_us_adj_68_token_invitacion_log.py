"""El log de acceso enmascara el token de las invitaciones (US-ADJ-68)."""

from __future__ import annotations

import logging

import pytest

from src.shared.frameworks.logging_config import FiltroTokens, enmascarar_tokens

_TOKEN = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefg"  # 43 caracteres, como `token_urlsafe(32)`
_UUID = "6f1c1c0e-1111-4222-8333-444455556666"


@pytest.mark.parametrize(
    "ruta",
    [
        "/api/identidad/invitaciones/",  # en producción, bajo `/api`
        "/identidad/invitaciones/",  # en local, sin prefijo
    ],
)
def test_enmascara_el_token_en_la_ruta_de_la_api(ruta: str) -> None:
    """Escenarios 1 y 2: el valor del token se reemplaza por `***`, con y sin el prefijo `/api`."""
    linea = f'127.0.0.1:5 - "GET {ruta}{_TOKEN} HTTP/1.1" 200'
    assert enmascarar_tokens(linea) == f'127.0.0.1:5 - "GET {ruta}*** HTTP/1.1" 200'


@pytest.mark.parametrize("estado", [200, 404, 422])
def test_conserva_metodo_y_estado(estado: int) -> None:
    """Escenario 3: solo cambia el token; el método y el código de estado siguen visibles."""
    original = f'"GET /api/identidad/invitaciones/{_TOKEN} HTTP/1.1" {estado}'
    resultado = enmascarar_tokens(original)
    assert resultado == f'"GET /api/identidad/invitaciones/*** HTTP/1.1" {estado}'
    assert _TOKEN not in resultado


def test_generar_una_invitacion_no_se_altera() -> None:
    """Escenario 4: `POST /comisiones/<uuid>/invitaciones` no tiene un segmento después."""
    linea = f'"POST /api/comisiones/{_UUID}/invitaciones HTTP/1.1" 201'
    assert enmascarar_tokens(linea) == linea


def test_las_otras_formas_de_token_siguen_enmascaradas() -> None:
    """Escenario 5: `token=` y `/recuperar-password/<token>` conviven con la ruta nueva."""
    linea = f"GET /registro?token={_TOKEN} | /recuperar-password/{_TOKEN} | /identidad/invitaciones/{_TOKEN}"
    assert enmascarar_tokens(linea) == (
        "GET /registro?token=*** | /recuperar-password/*** | /identidad/invitaciones/***"
    )


@pytest.mark.parametrize("corto", ["corto", "abc123", "A" * 19])
def test_un_segmento_corto_no_se_toca(corto: str) -> None:
    """Escenario 6: menos de 20 caracteres no es un token real."""
    linea = f'"GET /identidad/invitaciones/{corto} HTTP/1.1" 404'
    assert enmascarar_tokens(linea) == linea


def test_un_segmento_de_exactamente_20_caracteres_se_enmascara() -> None:
    """Borde del umbral: 20 caracteres ya cuentan como token."""
    assert enmascarar_tokens(f"/invitaciones/{'A' * 20}") == "/invitaciones/***"


def test_enmascara_varias_ocurrencias_en_el_mismo_texto() -> None:
    """Cada ocurrencia se enmascara, no solo la primera."""
    texto = f"/invitaciones/{_TOKEN} y /invitaciones/{_TOKEN[::-1]}"
    assert enmascarar_tokens(texto) == "/invitaciones/*** y /invitaciones/***"


def test_el_filtro_sanea_los_argumentos_como_lo_hace_uvicorn() -> None:
    """`uvicorn` pasa la ruta como argumento (`%s`): el mensaje formateado no trae el token."""
    registro = logging.LogRecord(
        "uvicorn.access",
        logging.INFO,
        __file__,
        1,
        '%s - "%s %s HTTP/%s" %d',
        ("1.2.3.4:5", "GET", f"/api/identidad/invitaciones/{_TOKEN}", "1.1", 404),
        None,
    )
    assert FiltroTokens().filter(registro) is True
    assert registro.getMessage() == '1.2.3.4:5 - "GET /api/identidad/invitaciones/*** HTTP/1.1" 404'
    assert _TOKEN not in registro.getMessage()
