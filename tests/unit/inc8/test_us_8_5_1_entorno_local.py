"""`ENTORNO=local`: valida solo el secreto y permite valores locales (US-8.5.1)."""

import pytest
from pydantic import ValidationError

from src.settings import Settings

_EJEMPLO = "cambiar-por-un-secreto-seguro"


def _crear(**cambios: str) -> Settings:
    base = {
        "entorno": "local",
        "database_url": "postgresql+asyncpg://u:p@localhost:5432/cognion",
        "secret_key": "x" * 40,
    }
    return Settings(**{**base, **cambios})  # type: ignore[arg-type]


def test_local_con_secreto_fuerte_y_valores_locales_arranca() -> None:
    """Escenario 1: secreto de 40 caracteres y todo en localhost/IP."""
    cfg = _crear(
        smtp_host="localhost",
        frontend_url="http://192.168.1.20:8000",
        cors_allowed_origins="http://192.168.1.20:8000,http://localhost:5173",
    )
    assert cfg.entorno == "local"


def test_local_con_secreto_de_ejemplo_falla_sin_imprimir_el_valor() -> None:
    """Escenario 2: nombra SECRET_KEY y no revela el valor."""
    with pytest.raises(ValidationError) as exc:
        _crear(secret_key=_EJEMPLO)
    assert "SECRET_KEY" in str(exc.value)
    assert _EJEMPLO not in str(exc.value)


def test_local_con_secreto_corto_falla() -> None:
    """Escenario 3: menos de 32 caracteres."""
    with pytest.raises(ValidationError) as exc:
        _crear(secret_key="corto-123")
    assert "SECRET_KEY" in str(exc.value)
    assert "corto-123" not in str(exc.value)


def test_desarrollo_con_secreto_de_ejemplo_arranca() -> None:
    """Escenario 4: sin cambios en desarrollo."""
    cfg = _crear(entorno="desarrollo", secret_key=_EJEMPLO)
    assert cfg.entorno == "desarrollo"


def test_produccion_sigue_rechazando_localhost() -> None:
    """Escenario 5: sin cambios en producción."""
    with pytest.raises(ValidationError) as exc:
        _crear(entorno="produccion")
    assert "DATABASE_URL no puede apuntar a localhost" in str(exc.value)
