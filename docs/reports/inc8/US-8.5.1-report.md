# Reporte — US-8.5.1: Entorno local con secreto fuerte para uso en red

**Estado:** implementada en `feature/US-8.5.1-entorno-local` (2026-10-18). PR diferido al cierre de la Iteración 5 (CI lento).
**Issue:** #536 · **Spec:** `docs/specs/inc8/US-8.5.1.md`

## Qué se hizo
- `Settings.entorno` admite `local` (además de `desarrollo`, `staging`, `produccion`).
- En `local` el validador comprueba **solo** el secreto: `SECRET_KEY` de al menos 32 caracteres y distinta del ejemplo. Permite localhost/IP en base, SMTP, `FRONTEND_URL` y CORS. El valor del secreto nunca aparece en el error.
- Se extrajo `_o_fallar()` para no duplicar el armado del error entre `local` y staging/producción. `desarrollo`, `staging` y `produccion` sin cambios de comportamiento.
- `.env.example` documenta `ENTORNO=local`.
- 5 tests unitarios (uno por escenario de la spec) en `tests/unit/inc8/test_us_8_5_1_entorno_local.py`.

## Decisiones
- Sin `.feature` (infra técnica, mismo precedente que `US-8.1.3`) y sin tests de integración (sin DB ni HTTP).
- Solo se corrió `tests/unit/`, para no tocar la base local.

## Calidad
Unit inc8 60/60, cobertura de `settings.py` 100 %, pylint 10.00, ruff/mypy 0 errores, MI 50.02, designreviewer 0 blocking. CC máx. 14 en `_validar_entorno_estricto`: preexistente, no la sube este cambio. CodeGuard full: 3 errores de tooling (vulture/codespell no instalados, timeout de mypy). Evidencia en `quality/reports/inc8/US-8.5.1-*.json`.
