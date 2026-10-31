# Reporte — US-8.1.1: CORS configurable por entorno

**Estado:** implementada en `feature/US-8.1.1-cors-configurable` (2026-10-16). PR diferido al cierre de la Iteración 1 del Incremento 8, por decisión de Víctor.
**Issue:** #514 · **Spec:** `docs/specs/inc8/US-8.1.1.md`

## Qué se hizo
- `Settings.cors_allowed_origins` (env `CORS_ALLOWED_ORIGINS`, default `http://localhost:5173`) y propiedad `cors_origins_list`.
- Validador que rechaza `*` (incompatible con `allow_credentials=True`): la app falla al arrancar.
- `src/app.py` toma los orígenes de `settings.cors_origins_list`.
- `.env.example` documenta la variable.

## Decisiones
- Sin `.feature` (infra técnica, mismo precedente que US-3.1.1 / US-6.1.1); los 4 escenarios de la spec quedan cubiertos por 6 tests unitarios.
- El test de preflight vive en `tests/unit/inc8/`: no usa base de datos, y el `conftest` de integración trunca tablas en cada test.

## Calidad
pylint 10.00, ruff y mypy 0 errores, CC máx 3, cobertura de `settings.py` 100%, suite unit 887/887.
CodeGuard (`--analysis-type full`, 9 checks): 13 errores, todos de tooling (vulture/codespell sin instalar, timeout de mypy `software_limpio#70`, `__init__.py` vacío); sin hallazgos de código. Detalle en `quality/reports/inc8/US-8.1.1-quality.json`.

## Pendiente
No cubre la validación fail-fast del resto de settings de producción (`US-8.1.3`) ni la URL base del frontend (`US-8.1.2`).
