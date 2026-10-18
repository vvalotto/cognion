# Contexto de Ejecución — US-8.5.4

## Fuentes
- **Fuente HU:** `docs/specs/inc8/US-8.5.4.md`, Issue [#539](https://github.com/vvalotto/cognion/issues/539)
- **Fuente Arquitectura:** `CLAUDE.md`, `ADR-022` (variante local), `US-8.5.3` (scripts/local)

## Historia de Usuario
- **ID:** US-8.5.4 — Backup y restauración local probada
- **Tipo:** tooling operativo (scripts en `scripts/local/`), sin código de producción
- **Puntos:** 3

## Decisiones de Ejecución
- **skip_bdd:** true — tooling de shell; verificación con `tests/uat/inc8/verificar_respaldo_local.sh` (mismo precedente que `US-8.5.3`).
- **Fases a ejecutar:** 0, 2, 3, 4 (verificación), 7, 8, 9. Sin 5/6.
- **Branch:** `feature/US-8.5.1-entorno-local` (apilada; PR único al cierre de la Iteración 5)

## Rutas
- Plan: docs/plans/inc8/US-8.5.4-plan.md · Reporte: docs/reports/inc8/US-8.5.4-report.md
- Quality: quality/reports/inc8/US-8.5.4-quality.json

## Notas
- La verificación usa una base descartable propia; no toca `cognion_local` ni la de desarrollo ni `~/CognionRespaldos` (carpeta temporal vía `COGNION_RESPALDOS`).
