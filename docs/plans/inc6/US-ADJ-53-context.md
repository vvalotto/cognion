# Contexto de Ejecución — US-ADJ-53

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-53.md` (aprobada por Víctor 2026-09-24), Issue #432
- **Fuente Arquitectura:** no aplica — tooling de tests del frontend

## Historia de Usuario
- **ID:** US-ADJ-53
- **Título:** Corrida de la suite frontend con cobertura estable, sin flags manuales
- **Tipo:** Configuración de tooling (sin código de producción)
- **Puntos:** 2 (estimado)
- **Prioridad:** Alta — antes de `US-ADJ-54` y `US-6.3.8`

## Decisiones de Ejecución
- **BDD:** Sí — 4 escenarios de la spec, validados por medición (corridas reales), no por Vitest
- **Fases a ejecutar:** 0, 1, 2 (con mediciones), 3, 7, 8, 9 — sin Fases 4-6 (no hay código que testear)

## Umbrales de calidad
- Cobertura frontend ≥ 80% (umbral ya configurado en `vite.config.ts`), `tsc -b` y `oxlint` 0 errores

## Rutas de Artefactos
- Contexto: `docs/plans/inc6/US-ADJ-53-context.md`
- BDD feature: `tests/features/inc6/US-ADJ-53-suite-cobertura-estable.feature`
- Plan: `docs/plans/inc6/US-ADJ-53-plan.md`
- Reporte: `docs/reports/inc6/US-ADJ-53-report.md`
- Quality report: `quality/reports/inc6/US-ADJ-53-quality.json`

## Notas propias de esta US
- Entorno: 8 núcleos, Vitest 4.1.10, Node 22.17. Vitest 4 usa `maxWorkers` (número o porcentaje) en `test`.
- **Gap detectado en Fase 0:** el comando de tests del frontend para la Fase 7 no está documentado en ningún lado
  (ni en `phase-7-quality-gates.md` ni en `WORKFLOW-DESARROLLO.md`): solo vive en los `quality.json` de cada US.
  Se agrega una sección "Frontend (perfil `clean-architecture-bc`)" en `phase-7-quality-gates.md`.
- CI (`ci.yml`) corre `npm run test` sin cobertura.
