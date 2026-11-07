"""Ningún `downgrade` de las migraciones borra una restricción sin nombre (US-8.3.4).

Alembic autogenera `op.create_foreign_key(None, ...)` y `op.drop_constraint(None, ...)`: el `upgrade`
funciona (PostgreSQL elige el nombre) pero el `downgrade` falla con "it has no name". La guarda corre
sin base de datos y se enciende con la próxima migración autogenerada que repita el patrón.
"""

from __future__ import annotations

import ast
from pathlib import Path

RAIZ_MIGRACIONES = Path(__file__).resolve().parents[3] / "migrations" / "versions"


def drops_sin_nombre(codigo: str) -> list[str]:
    """Llamadas `drop_constraint(None, ...)` dentro de un `downgrade`."""
    problemas: list[str] = []
    for funcion in ast.walk(ast.parse(codigo)):
        if not (isinstance(funcion, ast.FunctionDef) and funcion.name == "downgrade"):
            continue
        for nodo in ast.walk(funcion):
            if not (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute)):
                continue
            if nodo.func.attr != "drop_constraint" or not nodo.args:
                continue
            primero = nodo.args[0]
            if isinstance(primero, ast.Constant) and primero.value is None:
                problemas.append(f"línea {nodo.lineno}: drop_constraint(None, ...) no tiene nombre")
    return problemas


def test_la_guarda_detecta_un_drop_sin_nombre_y_acepta_uno_con_nombre() -> None:
    """La guarda no es decorativa."""
    mal = "def downgrade():\n    op.drop_constraint(None, 'estudiante', type_='foreignkey')\n"
    bien = "def downgrade():\n    op.drop_constraint('estudiante_comision_id_fkey', 'estudiante')\n"
    en_upgrade = "def upgrade():\n    op.drop_constraint(None, 'estudiante')\n"
    assert drops_sin_nombre(mal) != []
    assert drops_sin_nombre(bien) == []
    assert drops_sin_nombre(en_upgrade) == []  # solo importa el downgrade


def test_ninguna_migracion_borra_una_restriccion_sin_nombre() -> None:
    """Recorre las migraciones reales."""
    archivos = sorted(RAIZ_MIGRACIONES.glob("*.py"))
    assert len(archivos) >= 18, "no se encontraron las migraciones: la guarda no revisa nada"
    problemas = [
        f"{a.name}: {p}" for a in archivos for p in drops_sin_nombre(a.read_text(encoding="utf-8"))
    ]
    assert problemas == []
