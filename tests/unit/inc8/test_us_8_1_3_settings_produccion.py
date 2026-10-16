"""Validación fail-fast de `Settings` en staging/producción (US-8.1.3)."""

import pytest
from pydantic import ValidationError

from src.settings import Settings

_VALIDOS = {
    "database_url": "postgresql+asyncpg://u:p@cognion-db.flycast:5432/cognion",
    "secret_key": "x" * 40,
    "smtp_host": "smtp.ingenieria.uner.edu.ar",
    "smtp_from": "gestiondeproyectos@ingenieria.uner.edu.ar",
    "frontend_url": "https://cognion.fly.dev",
    "cors_allowed_origins": "https://cognion.fly.dev",
}


def _crear(**cambios: str) -> Settings:
    return Settings(**{**_VALIDOS, **cambios})  # type: ignore[arg-type]


def test_desarrollo_acepta_valores_de_ejemplo() -> None:
    """Sin `entorno`, los valores de desarrollo siguen siendo válidos."""
    cfg = Settings(database_url="postgresql://localhost/x", secret_key="t")
    assert cfg.entorno == "desarrollo"


@pytest.mark.parametrize("entorno", ["staging", "produccion"])
def test_entorno_estricto_con_todo_correcto_arranca(entorno: str) -> None:
    """Con la configuración completa, staging y producción arrancan."""
    assert _crear(entorno=entorno).entorno == entorno


def test_entorno_desconocido_falla() -> None:
    """Un `entorno` fuera del conjunto permitido es error."""
    with pytest.raises(ValidationError):
        _crear(entorno="otro")


@pytest.mark.parametrize(
    ("campo", "valor", "nombre"),
    [
        ("secret_key", "cambiar-por-un-secreto-seguro", "SECRET_KEY"),
        ("secret_key", "corta", "SECRET_KEY"),
        ("database_url", "postgresql+asyncpg://u:p@localhost:5432/c", "DATABASE_URL"),
        ("database_url", "postgresql+asyncpg://u:p@127.0.0.1/c", "DATABASE_URL"),
        ("smtp_host", "localhost", "SMTP_HOST"),
        ("smtp_from", "no-responder@cognion.local", "SMTP_FROM"),
        ("frontend_url", "http://localhost:5173", "FRONTEND_URL"),
        ("cors_allowed_origins", "https://a.fly.dev,http://localhost:5173", "CORS_ALLOWED_ORIGINS"),
    ],
)
def test_cada_regla_rechaza_en_produccion(campo: str, valor: str, nombre: str) -> None:
    """Cada valor de desarrollo se rechaza y el error nombra la variable."""
    with pytest.raises(ValidationError, match=nombre):
        _crear(entorno="produccion", **{campo: valor})


def test_reporta_todas_las_violaciones_juntas() -> None:
    """Varias fallas salen en un único error, para no corregir de a una."""
    with pytest.raises(ValidationError) as info:
        _crear(entorno="produccion", secret_key="corta", smtp_host="localhost")
    mensaje = str(info.value)
    assert "SECRET_KEY" in mensaje
    assert "SMTP_HOST" in mensaje


def test_el_error_no_filtra_el_secreto() -> None:
    """El valor del secreto nunca aparece en el mensaje."""
    secreto = "secreto-corto-visible"
    with pytest.raises(ValidationError) as info:
        Settings(
            entorno="produccion",
            database_url="postgresql://a@localhost/x",
            secret_key=secreto,
        )
    assert secreto not in str(info.value)
