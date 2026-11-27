"""Configuración común de la suite: aborta antes de vaciar una base que no sea descartable (VT-03)."""

import os
from pathlib import Path

import pytest

from tests.guarda_base import verificar_base_descartable

# `ADR-018` (enmendado, `US-12.2.5`): los tests corren cada paso en su propio event loop y no pueden reutilizar
# conexiones; piden `NullPool`. Va antes de que cualquier módulo importe `src.settings`.
os.environ["DB_POOL"] = "nula"

_CARPETAS_QUE_USAN_LA_BASE = ("integration", "step_defs", "uat")
_RAIZ_TESTS = Path(__file__).resolve().parent


def _usa_la_base(item: pytest.Item) -> bool:
    relativa = Path(str(item.path)).resolve().relative_to(_RAIZ_TESTS)
    return relativa.parts[0] in _CARPETAS_QUE_USAN_LA_BASE


def pytest_collection_finish(session: pytest.Session) -> None:
    """Si la corrida incluye tests que vacían la base, verifica que `DATABASE_URL` sea de prueba."""
    if any(_usa_la_base(item) for item in session.items):
        from src.settings import settings

        try:
            verificar_base_descartable(settings.database_url)
        except RuntimeError as error:
            raise pytest.UsageError(str(error)) from error
