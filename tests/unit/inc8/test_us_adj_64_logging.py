"""Logging de la aplicación y enmascarado de tokens (US-ADJ-64)."""

from __future__ import annotations

import logging
from collections.abc import Iterator

import pytest
from pydantic import ValidationError

from src.settings import Settings
from src.shared.frameworks.logging_config import (
    FiltroTokens,
    _HandlerCognion,
    configurar_logging,
    enmascarar_tokens,
)

_BASE = {
    "database_url": "postgresql+asyncpg://u:p@localhost:5432/cognion",
    "secret_key": "x" * 40,
}
_TOKEN_LARGO = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abc"


# ---------------------------------------------------------------- enmascarar_tokens


@pytest.mark.parametrize(
    ("original", "esperado"),
    [
        ("GET /registro?token=abc_DEF-123 HTTP/1.1", "GET /registro?token=*** HTTP/1.1"),
        (
            'WebSocket /api/x/canal?token=eyJhbGciOi.AAA.BBB&otro=1" [accepted]',
            'WebSocket /api/x/canal?token=***&otro=1" [accepted]',
        ),
        ("GET /?TOKEN=Mayusculas", "GET /?TOKEN=***"),
        (f"GET /recuperar-password/{_TOKEN_LARGO}", "GET /recuperar-password/***"),
    ],
)
def test_enmascara_el_token_y_deja_el_resto(original: str, esperado: str) -> None:
    """El valor del token se reemplaza por `***` y el resto de la línea queda igual."""
    assert enmascarar_tokens(original) == esperado


@pytest.mark.parametrize(
    "texto",
    [
        "POST /api/identidad/recuperar-password/solicitar",
        "POST /api/identidad/recuperar-password/confirmar",
        "GET /api/health",
        "Email (modo consola)\nPara: a@b.c",
        "",
    ],
)
def test_no_toca_lo_que_no_es_un_token(texto: str) -> None:
    """Las rutas de la API de recuperación y cualquier texto sin token pasan intactos."""
    assert enmascarar_tokens(texto) == texto


def test_enmascara_varios_tokens_en_la_misma_linea() -> None:
    """Cada ocurrencia se enmascara, no solo la primera."""
    assert enmascarar_tokens("a?token=1&b=2&token=3") == "a?token=***&b=2&token=***"


# ---------------------------------------------------------------- FiltroTokens


def _registro(msg: str, args: object) -> logging.LogRecord:
    return logging.LogRecord("uvicorn.error", logging.INFO, __file__, 1, msg, args, None)  # type: ignore[arg-type]


def test_el_filtro_sanea_los_argumentos_como_hace_uvicorn() -> None:
    """`uvicorn` pasa la ruta como argumento: el mensaje formateado no debe traer el token."""
    registro = _registro('%s - "WebSocket %s" [accepted]', ("1.2.3.4:5", "/canal?token=SECRETO"))
    assert FiltroTokens().filter(registro) is True
    assert registro.getMessage() == '1.2.3.4:5 - "WebSocket /canal?token=***" [accepted]'


def test_el_filtro_sanea_el_acceso_http_y_conserva_los_numeros() -> None:
    """El código de estado y los demás argumentos que no son texto no cambian."""
    registro = _registro(
        '%s - "%s %s HTTP/%s" %d', ("1.2.3.4:5", "GET", "/registro?token=SECRETO", "1.1", 200)
    )
    FiltroTokens().filter(registro)
    assert registro.getMessage() == '1.2.3.4:5 - "GET /registro?token=*** HTTP/1.1" 200'


def test_el_filtro_sanea_el_mensaje_sin_argumentos() -> None:
    """Un mensaje ya formateado también se enmascara."""
    registro = _registro("conexión ?token=SECRETO", ())
    FiltroTokens().filter(registro)
    assert registro.getMessage() == "conexión ?token=***"


def test_el_filtro_sanea_argumentos_con_nombre() -> None:
    """Los argumentos de un registro con diccionario también se sanean."""
    registro = _registro("%(ruta)s", ({"ruta": "/x?token=SECRETO"},))
    FiltroTokens().filter(registro)
    assert registro.getMessage() == "/x?token=***"


# ---------------------------------------------------------------- configurar_logging


@pytest.fixture
def logging_limpio() -> Iterator[None]:
    """Restaura el estado del logging que toca `configurar_logging`."""
    nombres = ("src", "uvicorn.access", "uvicorn.error")
    antes = {
        n: (
            logging.getLogger(n).level,
            list(logging.getLogger(n).handlers),
            list(logging.getLogger(n).filters),
        )
        for n in nombres
    }
    for n in nombres:
        logger = logging.getLogger(n)
        logger.handlers = [h for h in logger.handlers if not isinstance(h, _HandlerCognion)]
        logger.filters = [f for f in logger.filters if not isinstance(f, FiltroTokens)]
    yield
    for n, (nivel, handlers, filtros) in antes.items():
        logger = logging.getLogger(n)
        logger.setLevel(nivel)
        logger.handlers = handlers
        logger.filters = filtros


@pytest.mark.usefixtures("logging_limpio")
def test_configura_el_nivel_y_un_unico_handler_aunque_se_llame_dos_veces() -> None:
    """Es idempotente: no se acumulan handlers ni filtros."""
    configurar_logging("WARNING")
    configurar_logging("WARNING")
    src = logging.getLogger("src")
    assert src.level == logging.WARNING
    assert len([h for h in src.handlers if isinstance(h, _HandlerCognion)]) == 1
    for nombre in ("uvicorn.access", "uvicorn.error"):
        assert (
            len([f for f in logging.getLogger(nombre).filters if isinstance(f, FiltroTokens)]) == 1
        )


@pytest.mark.usefixtures("logging_limpio")
def test_el_nivel_se_puede_cambiar_en_una_segunda_llamada() -> None:
    """Volver a llamar con otro nivel lo actualiza sin duplicar el handler."""
    configurar_logging("INFO")
    configurar_logging("ERROR")
    assert logging.getLogger("src").level == logging.ERROR


@pytest.mark.usefixtures("logging_limpio")
def test_el_logger_de_smtp_queda_habilitado_para_info() -> None:
    """El logger que escribe el email de consola emite `INFO` (antes se descartaba)."""
    configurar_logging("INFO")
    assert logging.getLogger("src.shared.frameworks.smtp").isEnabledFor(logging.INFO)


@pytest.mark.usefixtures("logging_limpio")
def test_conserva_la_propagacion_para_que_caplog_siga_funcionando() -> None:
    """El logger `src` propaga al raíz: no se rompen los tests que usan `caplog`."""
    configurar_logging("INFO")
    assert logging.getLogger("src").propagate is True


# ---------------------------------------------------------------- Settings.log_level


@pytest.mark.parametrize("valor", ["DEBUG", "INFO", "WARNING", "ERROR"])
def test_log_level_acepta_los_valores_validos(valor: str) -> None:
    """Escenario 8: los cuatro niveles son válidos."""
    assert Settings(**_BASE, log_level=valor).log_level == valor


def test_log_level_por_defecto_es_info() -> None:
    """Sin la variable, el nivel es `INFO`."""
    assert Settings(**_BASE).log_level == "INFO"


def test_log_level_invalido_falla_y_lista_los_valores_validos() -> None:
    """Escenario 8: un valor inválido falla al cargar la configuración y dice cuáles son los válidos."""
    with pytest.raises(ValidationError) as error:
        Settings(**_BASE, log_level="ruidoso")
    mensaje = str(error.value)
    assert all(valor in mensaje for valor in ("DEBUG", "INFO", "WARNING", "ERROR"))
