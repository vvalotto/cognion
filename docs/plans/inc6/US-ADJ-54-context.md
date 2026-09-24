# Contexto de Ejecución — US-ADJ-54

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-54.md` (aprobada por Víctor 2026-09-24), Issue #433
- **Fuente Arquitectura:** no aplica — tests del frontend

## Historia de Usuario
- **ID:** US-ADJ-54
- **Título:** Esperas asincrónicas correctas en los tests del frontend
- **Tipo:** Tests (sin código de producción)
- **Puntos:** 3 (estimado)
- **Prioridad:** Alta — antes de `US-6.3.8`

## Decisiones de Ejecución
- **BDD:** Sí — 4 escenarios de la spec, validados por revisión del diff y corridas repetidas
- **Fases a ejecutar:** 0, 1, 2, 3, 7, 8, 9 — sin Fases 4-6 (los cambios son los propios tests)

## Umbrales de calidad
- `npm run test` y `npm run test:coverage` (`US-ADJ-53`) en verde, 3 corridas seguidas cada uno; `tsc -b`, `oxlint` 0 errores

## Rutas de Artefactos
- Contexto: `docs/plans/inc6/US-ADJ-54-context.md`
- BDD feature: `tests/features/inc6/US-ADJ-54-esperas-async-tests.feature`
- Plan: `docs/plans/inc6/US-ADJ-54-plan.md`
- Reporte: `docs/reports/inc6/US-ADJ-54-report.md`
- Quality report: `quality/reports/inc6/US-ADJ-54-quality.json`
