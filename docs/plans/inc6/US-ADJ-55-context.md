# Contexto de Ejecución — US-ADJ-55

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-55.md` (aprobada por Víctor 2026-09-24), Issue #437
- **Fuente Arquitectura:** no aplica — tooling de tests del frontend

## Historia de Usuario
- **ID:** US-ADJ-55
- **Título:** Espera máxima de Testing Library acorde a la suite completa
- **Tipo:** Configuración de tooling (sin código de producción)
- **Puntos:** 1 (estimado)
- **Prioridad:** Alta — antes de `US-6.3.9`

## Decisiones de Ejecución
- **BDD:** Sí — 4 escenarios de la spec, validados por medición (corridas reales), no por Vitest
- **Fases a ejecutar:** 0, 1, 2 (con mediciones), 3, 7, 8, 9 — sin Fases 4-6 (no hay código que testear)

## Umbrales de calidad
- Cobertura frontend ≥ 80% (umbral ya configurado en `vite.config.ts`), `tsc -b` y `oxlint` 0 errores

## Rutas de Artefactos
- Contexto: `docs/plans/inc6/US-ADJ-55-context.md`
- BDD feature: `tests/features/inc6/US-ADJ-55-espera-testing-library.feature`
- Plan: `docs/plans/inc6/US-ADJ-55-plan.md`
- Reporte: `docs/reports/inc6/US-ADJ-55-report.md`
- Quality report: `quality/reports/inc6/US-ADJ-55-quality.json`

## Notas propias de esta US
- Origen: fallo de `AutoregistroEstudiante` en la Fase 7 de `US-6.3.8` (`findByRole` agotó el `asyncUtilTimeout` de 1 s).
- Medición: envoltorio temporal de `asyncWrapper` en `setup.ts` (no commiteado). **Primera medición descartada:**
  `user-event` también pasa por `asyncWrapper`, así que `user.click`/`user.type` contaban como esperas; se repitió
  clasificando cada llamada por su stack.
