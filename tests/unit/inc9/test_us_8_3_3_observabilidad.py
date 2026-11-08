"""Logs estructurados y chequeo de readiness: formateador, configuración y salud (US-8.3.3)."""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from collections.abc import Iterator
from datetime import datetime

import pytest
from pydantic import ValidationError

from src.settings import Settings, settings
from src.shared.frameworks import salud
from src.shared.frameworks.logging_config import (
    FormateadorJson,
    configurar_logging,
    enmascarar_tokens,
)

JWT = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c3VhcmlvIn0.firma-del-token-de-prueba"
TOKEN_INVITACION = "swBlTw_WNuuqTQICj1eE-6XB--Vr-94FOwel2qfXeUQ"
CLAVE = "Secreta-2026-Muy-Larga"


def _registro(mensaje: str, *args: object, exc_info=None, nombre="src.prueba") -> logging.LogRecord:
    return logging.LogRecord(nombre, logging.INFO, __file__, 1, mensaje, args or None, exc_info)


@pytest.fixture
def logging_restaurado() -> Iterator[None]:
    """Devuelve los loggers `src` y de `uvicorn` a su estado original al terminar la prueba."""
    nombres = ("src", "uvicorn", "uvicorn.access", "uvicorn.error")
    guardado = {
        n: (
            list(logging.getLogger(n).handlers),
            list(logging.getLogger(n).filters),
            logging.getLogger(n).level,
        )
        for n in nombres
    }
    yield
    for nombre, (handlers, filtros, nivel) in guardado.items():
        logger = logging.getLogger(nombre)
        logger.handlers[:] = handlers
        logger.filters[:] = filtros
        logger.setLevel(nivel)


class TestFormateadorJson:
    """`FormateadorJson` escribe un objeto JSON por línea."""

    def test_trae_ts_nivel_logger_y_mensaje(self):
        """Trae ts nivel logger y mensaje."""
        linea = FormateadorJson().format(_registro("Hola %s", "mundo"))

        datos = json.loads(linea)
        assert set(datos) == {"ts", "nivel", "logger", "mensaje"}
        assert datos["nivel"] == "INFO"
        assert datos["logger"] == "src.prueba"
        assert datos["mensaje"] == "Hola mundo"
        assert datetime.fromisoformat(datos["ts"]).utcoffset().total_seconds() == 0

    def test_una_excepcion_sigue_siendo_una_sola_linea_con_el_campo_excepcion(self):
        """Una excepcion sigue siendo una sola linea con el campo excepcion."""
        try:
            raise ValueError("falló algo")
        except ValueError:
            registro = _registro("Se rompió", exc_info=sys.exc_info())

        linea = FormateadorJson().format(registro)

        assert "\n" not in linea
        datos = json.loads(linea)
        assert "ValueError: falló algo" in datos["excepcion"]
        assert "Traceback" in datos["excepcion"]

    def test_un_registro_sin_excepcion_no_trae_el_campo(self):
        """Un registro sin excepcion no trae el campo."""
        assert "excepcion" not in json.loads(FormateadorJson().format(_registro("normal")))

    def test_enmascara_los_tokens_del_mensaje(self):
        """Enmascara los tokens del mensaje."""
        linea = FormateadorJson().format(
            _registro(
                "GET /canal?token=%s y /identidad/invitaciones/%s",
                JWT,
                TOKEN_INVITACION,
            )
        )

        assert JWT not in linea and TOKEN_INVITACION not in linea
        assert json.loads(linea)["mensaje"].count("***") == 2

    def test_enmascara_los_tokens_del_traceback(self):
        """Enmascara los tokens del traceback."""
        try:
            raise RuntimeError(f"falló https://app/registro?token={JWT}")
        except RuntimeError:
            registro = _registro("error", exc_info=sys.exc_info())

        linea = FormateadorJson().format(registro)

        assert JWT not in linea
        assert "token=***" in json.loads(linea)["excepcion"]

    def test_los_caracteres_especiales_quedan_como_json_valido(self):
        """Los caracteres especiales quedan como json valido."""
        linea = FormateadorJson().format(_registro('Ñandú "con comillas"\ty\nsalto'))

        assert json.loads(linea)["mensaje"] == 'Ñandú "con comillas"\ty\nsalto'
        assert "\n" not in linea


class TestConfigurarLogging:
    """`configurar_logging` elige el formato y sigue siendo idempotente."""

    def _handler_de_src(self) -> logging.Handler:
        return next(
            h for h in logging.getLogger("src").handlers if type(h).__name__ == "_HandlerCognion"
        )

    def test_por_defecto_el_formato_es_texto(self, logging_restaurado):
        """Por defecto el formato es texto."""
        configurar_logging("INFO")

        linea = self._handler_de_src().format(_registro("hola"))

        assert linea == "INFO:     hola"

    def test_con_json_el_handler_de_src_escribe_json(self, logging_restaurado):
        """Con json el handler de src escribe json."""
        configurar_logging("INFO", "json")

        assert isinstance(self._handler_de_src().formatter, FormateadorJson)

    def test_es_idempotente_aunque_cambie_el_formato(self, logging_restaurado):
        """Es idempotente aunque cambie el formato."""
        for formato in ("texto", "json", "json", "texto"):
            configurar_logging("INFO", formato)

        propios = [
            h for h in logging.getLogger("src").handlers if type(h).__name__ == "_HandlerCognion"
        ]
        assert len(propios) == 1
        assert not isinstance(propios[0].formatter, FormateadorJson)

    def test_con_json_los_handlers_de_uvicorn_pasan_a_json(self, logging_restaurado):
        """Con json los handlers de uvicorn pasan a json."""
        ajeno = logging.StreamHandler()
        logging.getLogger("uvicorn.access").addHandler(ajeno)

        configurar_logging("INFO", "json")

        assert isinstance(ajeno.formatter, FormateadorJson)
        linea = ajeno.format(
            _registro(
                '%s - "GET %s HTTP/%s" %d',
                "127.0.0.1",
                "/x?token=" + JWT,
                "1.1",
                200,
                nombre="uvicorn.access",
            )
        )
        assert JWT not in linea
        assert json.loads(linea)["logger"] == "uvicorn.access"

    def test_con_json_tambien_cambia_el_handler_del_logger_padre_de_uvicorn(
        self, logging_restaurado
    ):
        # Los mensajes de arranque salen por `uvicorn.error`, que usa el handler del logger `uvicorn`.
        """Con json tambien cambia el handler del logger padre de uvicorn."""
        ajeno = logging.StreamHandler()
        logging.getLogger("uvicorn").addHandler(ajeno)

        configurar_logging("INFO", "json")

        assert isinstance(ajeno.formatter, FormateadorJson)

    def test_con_texto_no_toca_los_handlers_de_uvicorn(self, logging_restaurado):
        """Con texto no toca los handlers de uvicorn."""
        ajeno = logging.StreamHandler()
        formato_original = ajeno.formatter
        logging.getLogger("uvicorn.error").addHandler(ajeno)

        configurar_logging("INFO", "texto")

        assert ajeno.formatter is formato_original


class TestSettingsLogFormat:
    """`LOG_FORMAT` solo acepta `texto` o `json`."""

    def _crear(self, **extra):
        return Settings(
            _env_file=None,
            database_url="postgresql+asyncpg://u:p@h/d",
            secret_key="x" * 40,
            **extra,
        )

    def test_el_valor_por_defecto_es_texto(self):
        """El valor por defecto es texto."""
        assert self._crear().log_format == "texto"

    def test_json_es_valido(self):
        """Json es valido."""
        assert self._crear(log_format="json").log_format == "json"

    def test_otro_valor_impide_arrancar_y_el_mensaje_nombra_la_variable(self):
        """Otro valor impide arrancar y el mensaje nombra la variable."""
        with pytest.raises(ValidationError) as error:
            self._crear(log_format="xml")

        mensaje = str(error.value)
        assert "log_format" in mensaje
        assert "texto" in mensaje and "json" in mensaje


class TestSalud:
    """`base_disponible` y la limpieza de credenciales."""

    def test_sin_credenciales_quita_usuario_y_clave_de_una_url(self):
        """Sin credenciales quita usuario y clave de una url."""
        texto = "no se pudo conectar a postgresql+asyncpg://cognion:Secreta@db:5432/cognion"

        assert salud.sin_credenciales(texto) == (
            "no se pudo conectar a postgresql+asyncpg://***@db:5432/cognion"
        )

    def test_sin_credenciales_quita_la_clave_configurada_aunque_no_vaya_en_una_url(
        self, monkeypatch
    ):
        """Sin credenciales quita la clave configurada aunque no vaya en una url."""
        monkeypatch.setattr(settings, "database_url", f"postgresql+asyncpg://u:{CLAVE}@h/d")

        assert CLAVE not in salud.sin_credenciales(f"fallo con la clave {CLAVE} en el texto")

    async def test_responde_true_si_la_consulta_anda(self, monkeypatch):
        """Responde true si la consulta anda."""

        async def anda() -> None:
            """Anda."""
            return None

        monkeypatch.setattr(salud, "_consultar", anda)

        assert await salud.base_disponible() is True

    async def test_responde_false_y_registra_el_error_sin_credenciales(self, monkeypatch, caplog):
        """Responde false y registra el error sin credenciales."""
        monkeypatch.setattr(settings, "database_url", f"postgresql+asyncpg://u:{CLAVE}@h/d")

        async def falla() -> None:
            """Falla."""
            raise ConnectionRefusedError(f"conexión rechazada a postgresql://u:{CLAVE}@h/d")

        monkeypatch.setattr(salud, "_consultar", falla)

        with caplog.at_level(logging.ERROR, logger="src.shared.frameworks.salud"):
            resultado = await salud.base_disponible()

        assert resultado is False
        assert "ConnectionRefusedError" in caplog.text
        assert CLAVE not in caplog.text

    async def test_si_la_consulta_se_cuelga_responde_false_por_tiempo_agotado(
        self, monkeypatch, caplog
    ):
        """Si la consulta se cuelga responde false por tiempo agotado."""

        async def lenta() -> None:
            """Lenta."""
            await asyncio.sleep(5)

        monkeypatch.setattr(salud, "_consultar", lenta)

        with caplog.at_level(logging.ERROR, logger="src.shared.frameworks.salud"):
            resultado = await salud.base_disponible(tiempo_maximo=0.05)

        assert resultado is False
        assert "no respondió" in caplog.text

    async def test_la_dependencia_delega_en_base_disponible(self, monkeypatch):
        """La dependencia delega en base disponible."""

        async def siempre_false(*_args: object, **_kwargs: object) -> bool:
            """Siempre false."""
            return False

        monkeypatch.setattr(salud, "base_disponible", siempre_false)

        assert await salud.comprobar_base() is False

    def test_enmascarar_tokens_sigue_disponible_para_el_formateador(self):
        """Enmascarar tokens sigue disponible para el formateador."""
        assert "***" in enmascarar_tokens(f"?token={JWT}")
