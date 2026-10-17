"""Tests unitarios de `Settings.cors_origins_list` (US-8.1.1)."""

import pytest
from pydantic import ValidationError

from src.settings import Settings


def _settings(**kwargs: str) -> Settings:
    return Settings(database_url="postgresql://x", secret_key="k", **kwargs)


def test_default_es_solo_el_origen_de_desarrollo() -> None:
    """Sin variable definida solo se permite el origen de desarrollo."""
    assert _settings().cors_origins_list == ["http://localhost:5173"]


def test_varios_origenes_con_espacios_y_vacios() -> None:
    """Se separan por coma, se recortan espacios y se descartan vacíos."""
    cfg = _settings(cors_allowed_origins=" https://a.fly.dev , https://b.fly.dev,, ")
    assert cfg.cors_origins_list == ["https://a.fly.dev", "https://b.fly.dev"]


@pytest.mark.parametrize("valor", ["*", "https://a.fly.dev, *"])
def test_comodin_es_rechazado(valor: str) -> None:
    """`*` es incompatible con credenciales y falla al construir Settings."""
    with pytest.raises(ValidationError, match="no admite"):
        _settings(cors_allowed_origins=valor)
