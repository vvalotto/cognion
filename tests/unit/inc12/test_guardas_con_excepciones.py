"""Guardas con lista de excepciones del Incremento 12, Iteración 2 (Issue #666: `IM-03`, `IM-02`, `CA-01`).

Cada guarda fija hoy una deuda conocida: el número no puede crecer, y las historias que la pagan van vaciando la lista.
Las listas son exactas a propósito: si una historia baja un número, el test falla y obliga a actualizar la lista, así la
deuda declarada nunca queda por encima de la real.

- `IM-03`: ningún `commit()` fuera de los 8 archivos de hoy. Los vacía `US-12.2.1` (unidad de trabajo).
- `IM-02`: los `raise HTTPException` de los routers. Los baja `US-12.2.2` (errores de dominio traducidos en un solo lugar).
- `CA-01`: los gateways que importan los modelos ORM de `frameworks/`, y las excepciones de `import-linter`.
  Las vacía `US-12.2.3` (repositorios SQL en `frameworks/`).
"""

from __future__ import annotations

import ast
import re
import tomllib
from collections import Counter
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[3]
SRC = RAIZ / "src"

# --- IM-03: commit() fuera de una unidad de trabajo (21 hoy: 20 en repositorios y 1 en el event store) ---------------
COMMITS_PERMITIDOS: dict[str, int] = {
    "src/actividad_evaluativa/frameworks/event_store/sqlalchemy_event_store.py": 1,
    "src/banco_preguntas/interface_adapters/gateways/banco_repository.py": 1,
    "src/banco_preguntas/interface_adapters/gateways/materia_repository.py": 3,
    "src/banco_preguntas/interface_adapters/gateways/pregunta_repository.py": 2,
    "src/identidad/interface_adapters/gateways/comision_repository.py": 3,
    "src/identidad/interface_adapters/gateways/invitacion_repository.py": 4,
    "src/identidad/interface_adapters/gateways/token_recuperacion_password_repository.py": 4,
    "src/identidad/interface_adapters/gateways/usuario_repository.py": 3,
}

# --- IM-02: `raise HTTPException` en los routers (136 hoy, 19 archivos) -------------------------------------------------
# No cuenta las dependencias de autenticación (`dependencies.py`, `shared/.../require_rol.py`, `get_current_user.py`): ahí
# el 401/403 es legítimo y no es una traducción de un error de dominio.
HTTPEXCEPTION_EN_ROUTERS: dict[str, int] = {
    "src/actividad_evaluativa/frameworks/api/actividades_router.py": 14,
    "src/actividad_evaluativa/frameworks/api/evaluaciones_router.py": 10,
    "src/actividad_evaluativa/frameworks/api/revision_router.py": 2,
    "src/actividad_evaluativa/frameworks/api/sesiones_en_vivo_router.py": 32,
    "src/analytics/frameworks/api/analytics_router.py": 14,
    "src/banco_preguntas/frameworks/api/bancos_router.py": 2,
    "src/banco_preguntas/frameworks/api/materias_router.py": 5,
    "src/banco_preguntas/frameworks/api/preguntas_router.py": 12,
    "src/identidad/frameworks/api/auth_router.py": 3,
    "src/identidad/frameworks/api/autoregistro_router.py": 5,
    "src/identidad/frameworks/api/comisiones_router.py": 10,
    "src/identidad/frameworks/api/cuentas_router.py": 8,
    "src/identidad/frameworks/api/invitaciones_grupales_router.py": 7,
    "src/identidad/frameworks/api/invitaciones_router.py": 3,
    "src/identidad/frameworks/api/materias_comisiones_router.py": 2,
    "src/identidad/frameworks/api/perfil_router.py": 3,
    "src/identidad/frameworks/api/recuperacion_password_router.py": 1,
    "src/identidad/frameworks/api/registro_router.py": 1,
    "src/identidad/frameworks/api/usuarios_router.py": 2,
}

# --- CA-01: gateways SQL de `interface_adapters/` que importan los modelos ORM de `frameworks/` (10 hoy) ---------------
GATEWAYS_QUE_IMPORTAN_MODELOS: list[str] = [
    "src/banco_preguntas/interface_adapters/gateways/banco_repository.py",
    "src/banco_preguntas/interface_adapters/gateways/materia_repository.py",
    "src/banco_preguntas/interface_adapters/gateways/pregunta_repository.py",
    "src/identidad/interface_adapters/gateways/comision_query_repository.py",
    "src/identidad/interface_adapters/gateways/comision_repository.py",
    "src/identidad/interface_adapters/gateways/cuenta_query_repository.py",
    "src/identidad/interface_adapters/gateways/invitacion_repository.py",
    "src/identidad/interface_adapters/gateways/nombre_usuario_query_repository.py",
    "src/identidad/interface_adapters/gateways/token_recuperacion_password_repository.py",
    "src/identidad/interface_adapters/gateways/usuario_repository.py",
]

# --- CA-01: excepciones declaradas en los contratos de import-linter -----------------------------------------------------
IGNORE_IMPORTS_POR_CONTRATO: dict[str, list[str]] = {
    "Capas dentro de cada BC: entities <- use_cases <- interface_adapters <- frameworks": [
        "src.*.interface_adapters.gateways.** -> src.*.frameworks.db.models"
    ],
    "Aislamiento entre BC: solo frameworks/adapters puede importar de otro BC (ADR-006)": [
        "src.*.frameworks.adapters.** -> src.**"
    ],
    "shared no importa de ningún BC": [],
    "ADR-026: ningún BC salvo Analytics lee los modelos ORM de otro BC": [
        "src.identidad.** -> src.identidad.frameworks.db.models",
        "src.actividad_evaluativa.** -> src.actividad_evaluativa.frameworks.db.models",
        "src.banco_preguntas.** -> src.banco_preguntas.frameworks.db.models",
    ],
}


def _relativo(ruta: Path) -> str:
    return ruta.relative_to(RAIZ).as_posix()


def contar_commits(codigo: str) -> int:
    """Cantidad de llamadas `.commit()` en un fuente."""
    return sum(
        isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "commit"
        for n in ast.walk(ast.parse(codigo))
    )


def contar_http_exception(codigo: str) -> int:
    """Cantidad de `raise HTTPException(...)` (con o sin `from`) en un fuente."""
    cuenta = 0
    for nodo in ast.walk(ast.parse(codigo)):
        if isinstance(nodo, ast.Raise) and isinstance(nodo.exc, ast.Call):
            llamado = nodo.exc.func
            if getattr(llamado, "id", getattr(llamado, "attr", None)) == "HTTPException":
                cuenta += 1
    return cuenta


def importa_modelos_orm(codigo: str) -> bool:
    """¿Importa `src.<bc>.frameworks.db.models`?"""
    return bool(re.search(r"from src\.\w+\.frameworks\.db\.models import", codigo))


def _real(contador, archivos) -> dict[str, int]:
    cuenta: Counter[str] = Counter()
    for archivo in archivos:
        n = contador(archivo.read_text(encoding="utf-8"))
        if n:
            cuenta[_relativo(archivo)] = n
    return dict(sorted(cuenta.items()))


def _explicar(esperado: dict, real: dict, que: str, historia: str) -> str:
    sube = {k: (esperado.get(k, 0), v) for k, v in real.items() if v > esperado.get(k, 0)}
    baja = {k: (v, real.get(k, 0)) for k, v in esperado.items() if real.get(k, 0) < v}
    return (
        f"{que}: la lista de excepciones no coincide con el código.\n"
        f"  Aumentó (esperado, real) — no se agrega deuda nueva: {sube}\n"
        f"  Bajó (esperado, real) — bien: actualizá la lista de este test ({historia}): {baja}"
    )


class TestGuardaDeCommits:
    """`IM-03`: la transacción la maneja una unidad de trabajo, no cada repositorio."""

    def test_los_commit_son_exactamente_los_declarados(self) -> None:
        real = _real(contar_commits, SRC.rglob("*.py"))
        assert real == COMMITS_PERMITIDOS, _explicar(
            COMMITS_PERMITIDOS, real, "commit()", "US-12.2.1"
        )

    def test_el_total_declarado_es_el_del_informe(self) -> None:
        assert sum(COMMITS_PERMITIDOS.values()) == 21

    def test_detecta_un_commit_nuevo(self) -> None:
        assert contar_commits("async def f(s):\n    await s.commit()\n") == 1
        assert contar_commits("def f(s):\n    s.flush()\n") == 0


class TestGuardaDeHttpException:
    """`IM-02`: los routers dejan de traducir errores de dominio a mano; el número solo puede bajar."""

    def test_los_raise_httpexception_son_exactamente_los_declarados(self) -> None:
        routers = [p for p in SRC.glob("*/frameworks/api/*.py")]
        real = _real(contar_http_exception, routers)
        assert real == HTTPEXCEPTION_EN_ROUTERS, _explicar(
            HTTPEXCEPTION_EN_ROUTERS, real, "raise HTTPException", "US-12.2.2"
        )

    def test_el_total_declarado_es_el_medido(self) -> None:
        assert sum(HTTPEXCEPTION_EN_ROUTERS.values()) == 136

    def test_detecta_un_raise_con_from_y_sin_from(self) -> None:
        codigo = (
            "def f():\n"
            "    try:\n        g()\n"
            "    except E as exc:\n        raise HTTPException(status_code=404) from exc\n"
            "    raise HTTPException(status_code=403)\n"
        )
        assert contar_http_exception(codigo) == 2
        assert contar_http_exception("def f():\n    raise ValueError('x')\n") == 0


class TestGuardaDeCapasYRepositorios:
    """`CA-01`: los repositorios SQL pasan a `frameworks/`; hasta entonces la excepción está acotada."""

    def test_los_gateways_que_importan_modelos_son_los_declarados(self) -> None:
        real = sorted(
            _relativo(p)
            for p in SRC.glob("*/interface_adapters/gateways/*.py")
            if importa_modelos_orm(p.read_text(encoding="utf-8"))
        )
        assert real == GATEWAYS_QUE_IMPORTAN_MODELOS, (
            "Los gateways que importan los modelos ORM no coinciden con la lista. "
            f"Nuevos: {sorted(set(real) - set(GATEWAYS_QUE_IMPORTAN_MODELOS))}; "
            f"ya no lo hacen (actualizá la lista, US-12.2.3): {sorted(set(GATEWAYS_QUE_IMPORTAN_MODELOS) - set(real))}"
        )

    def test_las_excepciones_de_import_linter_son_las_declaradas(self) -> None:
        contratos = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))["tool"][
            "importlinter"
        ]["contracts"]
        real = {c["name"]: c.get("ignore_imports", []) for c in contratos}
        assert real == IGNORE_IMPORTS_POR_CONTRATO

    @pytest.mark.parametrize("nombre", sorted(IGNORE_IMPORTS_POR_CONTRATO))
    def test_cada_contrato_esta_declarado(self, nombre: str) -> None:
        assert nombre in IGNORE_IMPORTS_POR_CONTRATO

    def test_detecta_un_import_de_modelos(self) -> None:
        assert importa_modelos_orm("from src.identidad.frameworks.db.models import UsuarioModel\n")
        assert not importa_modelos_orm("from src.identidad.entities.usuario import Usuario\n")
