"""Guarda de la base de datos de los tests (hallazgo VT-03 del Incremento 12).

Los tests de integración, BDD y UAT vacían las tablas de la base a la que apunta `DATABASE_URL`.
Esta guarda corta la corrida si esa base no es descartable, es decir, si su nombre no termina en `_test`.
"""

from sqlalchemy.engine import make_url

SUFIJO_BASE_DESCARTABLE = "_test"


def verificar_base_descartable(database_url: str) -> None:
    """Lanza `RuntimeError` si la base de `database_url` no es descartable."""
    nombre = make_url(database_url).database or ""
    if not nombre.endswith(SUFIJO_BASE_DESCARTABLE):
        raise RuntimeError(
            f"La base '{nombre}' no termina en '{SUFIJO_BASE_DESCARTABLE}': estos tests vacían sus tablas. "
            f"Usá una base descartable, por ejemplo DATABASE_URL=postgresql+asyncpg://.../cognion_test pytest ..."
        )
