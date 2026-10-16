# Contexto de Ejecución — US-8.1.2

## Fuentes
- **Fuente HU:** `docs/specs/inc8/US-8.1.2.md`, Issue [#515](https://github.com/vvalotto/cognion/issues/515)
- **Fuente Arquitectura:** `CLAUDE.md`, `ADR-021`, `ADR-024`

## Historia de Usuario
- **ID:** US-8.1.2 — URL base de API y WebSocket en build
- **Tipo:** infra frontend técnica, sin comando de negocio
- **Puntos:** 2

## Decisiones de Ejecución
- **skip_bdd:** true — mismo precedente que `US-3.1.1`/`US-6.1.1` (infra técnica): los 4
  escenarios de la spec se cubren con tests unitarios/integración, sin `.feature`.
- **Fases a ejecutar:** 0, 2, 3, 4, 7, 8, 9 (frontend puro; Vitest cubre unit e integración)

## Perfil Activo
- clean-architecture-bc; umbrales: oxlint 0 errores, tsc -b 0 errores, cobertura de config.ts 100%

## Rutas
- Plan: docs/plans/inc8/US-8.1.2-plan.md
- Reporte: docs/reports/inc8/US-8.1.2-report.md
- Quality: quality/reports/inc8/US-8.1.2-quality.json

## Notas
- Frontend puro: sin riesgo para la base. Sin prettier (memoria del proyecto).
