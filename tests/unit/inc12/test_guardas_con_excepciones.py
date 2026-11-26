"""Guardas con lista de excepciones del Incremento 12, Iteración 2 (Issue #666: `IM-03`, `IM-02`, `CA-01`).

Cada guarda fija hoy una deuda conocida: el número no puede crecer, y las historias que la pagan van vaciando la lista.
Las listas son exactas a propósito: si una historia baja un número, el test falla y obliga a actualizar la lista, así la
deuda declarada nunca queda por encima de la real.

- `IM-03`: ningún `commit()` fuera de la unidad de trabajo (`shared/frameworks/db.py`) y del event store, la única excepción de `ADR-028`. Lo cumplió `US-12.2.1`.
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

# --- IM-03: commit() fuera de la unidad de trabajo. Desde `US-12.2.1` solo ella y el event store (`ADR-028`) ---------
COMMITS_PERMITIDOS: dict[str, int] = {
    "src/actividad_evaluativa/frameworks/event_store/sqlalchemy_event_store.py": 1,
    # La unidad de trabajo misma: confirma al salir bien y ante un error controlado (dos caminos).
    "src/shared/frameworks/db.py": 2,
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
GATEWAYS_QUE_IMPORTAN_MODELOS: list[str] = []

# --- CA-01: excepciones declaradas en los contratos de import-linter -----------------------------------------------------
IGNORE_IMPORTS_POR_CONTRATO: dict[str, list[str]] = {
    "Capas dentro de cada BC: entities <- use_cases <- interface_adapters <- frameworks": [],
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

    def test_solo_la_unidad_de_trabajo_y_el_event_store_confirman(self) -> None:
        assert sorted(COMMITS_PERMITIDOS) == [
            "src/actividad_evaluativa/frameworks/event_store/sqlalchemy_event_store.py",
            "src/shared/frameworks/db.py",
        ]

    def test_detecta_un_commit_nuevo(self) -> None:
        assert contar_commits("async def f(s):\n    await s.commit()\n") == 1
        assert contar_commits("def f(s):\n    s.flush()\n") == 0


# --- IM-03: casos de uso que escriben y después levantan un error (`ADR-028`, enmienda del 2026-11-26) --------------------
# La unidad de trabajo confirma ante un error controlado, así que estos tres siguen funcionando (el intento fallido de login
# se cuenta y el bloqueo de cuenta rige, `INV-ID-10` e `INV-ID-21`). Un caso nuevo debe ser una decisión consciente.
ESCRIBEN_Y_LUEGO_LEVANTAN: dict[str, list[str]] = {
    "src/identidad/use_cases/cambiar_password.py": ["execute"],
    "src/identidad/use_cases/iniciar_sesion.py": ["execute"],
    "src/identidad/use_cases/politica_bloqueo.py": ["rechazar_si_bloqueada"],
}
_METODOS_DE_ESCRITURA = {
    "guardar",
    "actualizar",
    "eliminar",
    "eliminar_de",
    "reemplazar",
    "incrementar_usos",
    "invalidar_activos_de",
}


def funciones_que_escriben_y_luego_levantan(codigo: str) -> list[str]:
    """Nombres de las funciones con una escritura por repositorio seguida (más abajo) de un `raise`."""
    nombres: list[str] = []
    for funcion in ast.walk(ast.parse(codigo)):
        if not isinstance(funcion, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        lineas_de_escritura: list[int] = []
        lineas_de_raise: list[int] = []
        for nodo in ast.walk(funcion):
            if isinstance(nodo, ast.Raise):
                lineas_de_raise.append(nodo.lineno)
            elif (
                isinstance(nodo, ast.Await)
                and isinstance(nodo.value, ast.Call)
                and isinstance(nodo.value.func, ast.Attribute)
                and nodo.value.func.attr in _METODOS_DE_ESCRITURA
                and any(
                    k in ast.unparse(nodo.value.func.value)
                    for k in ("repositorio", "repository", "repo")
                )
            ):
                lineas_de_escritura.append(nodo.lineno)
        if lineas_de_escritura and any(r > min(lineas_de_escritura) for r in lineas_de_raise):
            nombres.append(funcion.name)
    return nombres


class TestGuardaDeEscribirYLuegoLevantar:
    """`IM-03`: un error controlado deja confirmado lo escrito antes de levantarse; solo hay 3 casos y son intencionales."""

    def test_los_casos_que_escriben_y_luego_levantan_son_los_declarados(self) -> None:
        real: dict[str, list[str]] = {}
        for archivo in SRC.glob("*/use_cases/*.py"):
            nombres = funciones_que_escriben_y_luego_levantan(archivo.read_text(encoding="utf-8"))
            if nombres:
                real[_relativo(archivo)] = sorted(nombres)
        assert real == dict(sorted(ESCRIBEN_Y_LUEGO_LEVANTAN.items())), (
            "Un caso de uso escribe y después levanta un error: con la unidad de trabajo, si el error es controlado se "
            f"confirma lo escrito. Declaralo con una justificación. Real: {real}"
        )

    def test_detecta_una_escritura_seguida_de_un_raise(self) -> None:
        codigo = (
            "async def f(self):\n"
            "    await self._usuario_repositorio.actualizar(u)\n"
            "    raise ValueError()\n"
        )
        assert funciones_que_escriben_y_luego_levantan(codigo) == ["f"]

    def test_no_marca_un_raise_previo_a_la_escritura(self) -> None:
        codigo = (
            "async def f(self):\n"
            "    if x:\n        raise ValueError()\n"
            "    await self._usuario_repositorio.guardar(u)\n"
        )
        assert funciones_que_escriben_y_luego_levantan(codigo) == []


class TestGuardaDeLaSesion:
    """`US-12.2.1`: la sesión del request sale de un único `SessionDep` de `shared/`."""

    def test_ningun_contexto_define_su_propio_session_dep(self) -> None:
        propios = [
            _relativo(archivo)
            for archivo in SRC.glob("*/frameworks/dependencies.py")
            if re.search(r"^SessionDep\s*=", archivo.read_text(encoding="utf-8"), re.MULTILINE)
        ]
        assert propios == []

    def test_ningun_repositorio_confirma_la_transaccion(self) -> None:
        for archivo in [
            *SRC.glob("*/interface_adapters/gateways/*.py"),
            *SRC.glob("*/frameworks/repositories/*.py"),
        ]:
            assert contar_commits(archivo.read_text(encoding="utf-8")) == 0, _relativo(archivo)


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

    def test_todo_repositorio_sql_vive_en_frameworks_repositories(self) -> None:
        """`ADR-030`: `*_repository.py` y `email_unico.py` solo bajo `frameworks/repositories/`."""
        fuera = sorted(
            _relativo(p)
            for patron in ("*_repository.py", "email_unico.py")
            for p in SRC.glob(f"*/**/{patron}")
            if p.parent.name != "repositories" or p.parent.parent.name != "frameworks"
        )
        assert fuera == [], f"Repositorios fuera de frameworks/repositories/: {fuera}"

    def test_frameworks_adapters_no_contiene_repositorios(self) -> None:
        assert sorted(_relativo(p) for p in SRC.glob("*/frameworks/adapters/*_repository.py")) == []

    def test_no_existe_interface_adapters_gateways(self) -> None:
        assert sorted(_relativo(p) for p in SRC.glob("*/interface_adapters/gateways")) == []

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
