# 02 · Conformidad arquitectónica

> Pregunta: ¿el código cumple las reglas de capas que el proyecto declara no negociables?

## Qué se miró

- `uv run lint-imports` sobre `develop` (4 contratos de `[tool.importlinter]` en `pyproject.toml`).
- Búsqueda de imports de FastAPI, SQLAlchemy, Pydantic, PyJWT y Starlette en `entities/` y `use_cases/`.
- Ubicación de repositorios, modelos ORM y adaptadores en cada contexto.

## Fortalezas

- **Los 4 contratos se cumplen**: 329 archivos y 1.085 dependencias analizadas, 0 contratos rotos.
- **Las capas internas están limpias de frameworks**: ningún import de FastAPI, SQLAlchemy, Pydantic ni PyJWT en `entities/` ni en `use_cases/` de ningún contexto.
- **La regla tiene un test que prueba que falla**: `tests/unit/inc9/test_guarda_arquitectura.py` siembra una violación por contrato. Es poco común y vale mucho: una guarda que nunca se vio fallar no es una guarda.
- **Tipado estricto real**: 0 `type: ignore` y 1 solo `noqa` en todo `src/`.

## Hallazgos

### CA-01 · Dos convenciones para ubicar los repositorios SQL

- **Vara:** Conformidad · **Severidad:** Media · **Confianza:** Verificado · **Esfuerzo:** M
- **Evidencia:**
  - Identidad y Banco de Preguntas tienen sus repositorios en `interface_adapters/gateways/` (10 archivos), que importan los modelos ORM de `frameworks/db/models.py`.
  - Actividad Evaluativa y Analytics los tienen en `frameworks/adapters/` y `frameworks/event_store/`, sin esa inversión.
  - El contrato de capas declara la excepción: `"src.*.interface_adapters.gateways.** -> src.*.frameworks.db.models"` (10 imports ignorados).
- **Por qué importa:** la excepción hace que una capa interna dependa de una externa, que es justo lo que la regla prohíbe. Además el proyecto tiene dos respuestas a la misma pregunta ("¿dónde va un repositorio?"), según cuándo se escribió el contexto.
- **Recomendación:** mover los 10 repositorios de Identidad y Banco a `frameworks/`, como ya hacen los contextos más nuevos, y borrar la excepción de `ignore_imports`. Es un cambio mecánico, protegido por `import-linter` y por los tests de integración.

### CA-02 · La versión de Python validada no es la que corre

- **Vara:** Conformidad · **Severidad:** Baja · **Confianza:** Verificado · **Esfuerzo:** S
- **Evidencia:**
  - `pyproject.toml`: `requires-python = ">=3.11"`, `target-version = "py311"` (black y ruff) y `python_version = "3.11"` (mypy).
  - `.github/workflows/ci.yml` usa `python-version: "3.12"` en sus tres jobs y el `Dockerfile` parte de `python:3.12-slim`.
  - `CLAUDE.md` declara "Python 3.11".
- **Por qué importa:** mypy valida el código como 3.11 y el sistema corre en 3.12. El riesgo práctico es bajo, pero la versión declarada dejó de ser un dato confiable.
- **Recomendación:** fijar 3.12 en `pyproject.toml` y en `CLAUDE.md`.

### CA-03 · El contrato de capas no dice nada sobre qué datos cruzan

- **Vara:** Decisión · **Severidad:** Media · **Confianza:** Verificado · **Esfuerzo:** se resuelve con IM-01
- **Evidencia:** el contrato `layers` permite que `frameworks/` importe cualquier capa interna. Los routers importan entidades y errores de dominio directamente; por ejemplo [`sesiones_en_vivo_router.py`](../../src/actividad_evaluativa/frameworks/api/sesiones_en_vivo_router.py) importa el agregado `ActividadEvaluativaEnVivo` y 22 excepciones de `entities/errors.py`.
- **Por qué importa:** la regla de dependencia se cumple, pero la capa `interface_adapters/` no traduce nada: las entidades salen del caso de uso, atraviesan el controller sin tocarse y llegan al router. La conformidad mecánica es total; la separación que la regla busca es parcial.
- **Recomendación:** ver [IM-01](05-implementacion-por-capa.md#im-01--los-controllers-no-cumplen-ninguna-función).

## Juicio

La regla de dependencia se cumple y está bien custodiada. Lo que queda es deuda de uniformidad (CA-01) y un límite de la propia regla: `import-linter` controla la dirección de los imports, no qué viaja por ellos. Ese límite reaparece, con más peso, en el [capítulo 03](03-acoplamiento-entre-contextos.md).
