"""`US-12.2.5` (`IM-06`, `ADR-018` enmendado): el pool de conexiones sale de la configuración.

`NullPool` existe por los tests (cada paso del BDD corre en su propio event loop); en ejecución hay un solo
loop y se usa un pool normal. Los tests piden `NullPool` con `DB_POOL=nula` desde `tests/conftest.py`.
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool

from src.settings import Settings
from src.shared.frameworks.db import crear_motor

URL = "postgresql+asyncpg://user:password@localhost:5432/cognion_test"


def _config(**cambios: object) -> Settings:
    return Settings(database_url=URL, secret_key="x" * 40, **cambios)  # type: ignore[arg-type]


def test_el_valor_por_defecto_es_el_pool_porque_la_ejecucion_real_lo_usa() -> None:
    assert Settings.model_fields["db_pool"].default == "cola"


def test_la_suite_corre_con_pool_nulo() -> None:
    """`tests/conftest.py` fija `DB_POOL=nula` antes de importar cualquier módulo de `src`."""
    assert os.environ.get("DB_POOL") == "nula"


def test_con_pool_nulo_el_motor_no_retiene_conexiones() -> None:
    motor = crear_motor(_config(db_pool="nula"))

    assert isinstance(motor.pool, NullPool)


def test_con_pool_el_motor_usa_los_parametros_de_la_configuracion() -> None:
    motor = crear_motor(
        _config(db_pool="cola", db_pool_size=4, db_max_overflow=7, db_pool_timeout=12)
    )

    pool = motor.pool
    assert isinstance(pool, AsyncAdaptedQueuePool)
    assert pool.size() == 4
    assert pool._max_overflow == 7  # noqa: SLF001
    assert pool._timeout == 12  # noqa: SLF001
    assert pool._pre_ping is True  # noqa: SLF001


def test_los_parametros_por_defecto_son_los_acordados() -> None:
    config = _config(db_pool="cola")

    assert (config.db_pool_size, config.db_max_overflow, config.db_pool_timeout) == (10, 20, 30)


@pytest.mark.parametrize("valor", ["otra", "", "NullPool"])
def test_un_valor_desconocido_de_db_pool_se_rechaza(valor: str) -> None:
    with pytest.raises(ValueError):
        _config(db_pool=valor)
