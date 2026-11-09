"""Steps BDD de US-8.3.4 — `alembic downgrade base` funciona.

Corren `alembic` real contra una base descartable propia (nunca la de `DATABASE_URL`) y la borran al
terminar; si ningún rol puede crear bases de datos, se saltean con aviso.
"""

from __future__ import annotations

import subprocess
from collections.abc import Iterator
from typing import Any

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.unit.inc9._base_descartable import BaseDescartable

scenarios("../../features/inc9/US-8.3.4-downgrade-base.feature")


@pytest.fixture
def ctx() -> Iterator[dict[str, Any]]:
    """Estado del escenario; borra la base descartable al terminar."""
    base = BaseDescartable()
    estado: dict[str, Any] = {"base": base, "resultados": []}
    yield estado
    base.borrar()


def _migrar(ctx: dict[str, Any], destino: str) -> subprocess.CompletedProcess[str]:
    base: BaseDescartable = ctx["base"]
    base.crear()
    resultado = base.alembic("upgrade", destino)
    assert resultado.returncode == 0, resultado.stderr[-500:]
    ctx["revision_inicial"] = base.revision_actual()
    return resultado


# ---------------------------------------------------------------- Given


@given("una base descartable migrada hasta la última revisión")
def base_en_head(ctx: dict[str, Any]) -> None:
    """Crea la base y la migra hasta `head`."""
    _migrar(ctx, "head")


@given(
    parsers.parse('una base descartable migrada hasta la revisión "{revision}"'),
)
def base_en_revision(ctx: dict[str, Any], revision: str) -> None:
    """Crea la base y la migra hasta una revisión concreta."""
    _migrar(ctx, revision)


# ---------------------------------------------------------------- When


@when("se deshacen todas las migraciones hasta la base vacía")
def deshacer_todo(ctx: dict[str, Any]) -> None:
    """`alembic downgrade base`."""
    ctx["resultado"] = ctx["base"].alembic("downgrade", "base")
    ctx["resultados"].append(ctx["resultado"])


@when("se vuelve a migrar hasta la última revisión")
def migrar_de_nuevo(ctx: dict[str, Any]) -> None:
    """`alembic upgrade head`."""
    ctx["resultado"] = ctx["base"].alembic("upgrade", "head")
    ctx["resultados"].append(ctx["resultado"])


@when("se deshace una migración")
def deshacer_una(ctx: dict[str, Any]) -> None:
    """`alembic downgrade -1`."""
    ctx["resultado"] = ctx["base"].alembic("downgrade", "-1")
    ctx["resultados"].append(ctx["resultado"])


# ---------------------------------------------------------------- Then


@then("la operación termina sin error")
def sin_error(ctx: dict[str, Any]) -> None:
    """El subproceso de `alembic` terminó con código 0."""
    assert ctx["resultado"].returncode == 0, ctx["resultado"].stderr[-800:]


@then("todas las operaciones terminaron sin error")
def todas_sin_error(ctx: dict[str, Any]) -> None:
    """Cada comando de `alembic` del escenario terminó con código 0."""
    assert ctx["resultados"], "el escenario no ejecutó ninguna operación"
    for resultado in ctx["resultados"]:
        assert resultado.returncode == 0, resultado.stderr[-800:]


@then("no quedan tablas de la aplicación")
def sin_tablas(ctx: dict[str, Any]) -> None:
    """Solo queda `alembic_version`."""
    tablas = ctx["base"].consulta(
        "SELECT string_agg(tablename, ',') FROM pg_tables "
        "WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
    )
    assert tablas == ""


@then("la base queda en la misma revisión que antes")
def misma_revision(ctx: dict[str, Any]) -> None:
    """La revisión actual coincide con la inicial."""
    assert ctx["base"].revision_actual() == ctx["revision_inicial"]


@then(parsers.parse('la clave foránea de la comisión del estudiante se llama "{nombre}"'))
def nombre_de_la_fk(ctx: dict[str, Any], nombre: str) -> None:
    """El nombre que asigna PostgreSQL es el que usa el `downgrade`."""
    encontrado = ctx["base"].consulta(
        "SELECT conname FROM pg_constraint WHERE conrelid = 'estudiante'::regclass "
        "AND contype = 'f' AND pg_get_constraintdef(oid) LIKE '%(comision_id)%'"
    )
    assert encontrado == nombre


@then("la tabla de estudiantes ya no tiene la columna de la comisión")
def sin_columna(ctx: dict[str, Any]) -> None:
    """La migración deshecha borró `estudiante.comision_id`."""
    columnas = ctx["base"].consulta(
        "SELECT string_agg(column_name, ',') FROM information_schema.columns "
        "WHERE table_name = 'estudiante'"
    )
    assert "comision_id" not in columnas.split(",")
