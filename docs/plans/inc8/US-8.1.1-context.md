# Contexto de Ejecución — US-8.1.1

## Fuentes
- **Fuente HU:** `docs/specs/inc8/US-8.1.1.md`, Issue [#514](https://github.com/vvalotto/cognion/issues/514)
- **Fuente Arquitectura:** `CLAUDE.md`, `ADR-021`, `ADR-024`

## Historia de Usuario
- **ID:** US-8.1.1 — CORS configurable por entorno
- **Tipo:** infra backend técnica, sin comando de negocio
- **Puntos:** 2

## Decisiones de Ejecución
- **skip_bdd:** true — mismo precedente que `US-3.1.1`/`US-6.1.1` (infra técnica): los 4
  escenarios de la spec se cubren con tests unitarios/integración, sin `.feature`.
- **Fases a ejecutar:** 0, 2, 3, 4, 5, 7, 8, 9

## Perfil Activo
- clean-architecture-bc; umbrales: pylint ≥ 8.0, CC ≤ 10, MI ≥ 20, cobertura ≥ 95%

## Rutas
- Plan: docs/plans/inc8/US-8.1.1-plan.md
- Reporte: docs/reports/inc8/US-8.1.1-report.md
- Quality: quality/reports/inc8/US-8.1.1-quality.json

## Notas
- No correr pytest contra la base de desarrollo: usar `DATABASE_URL` descartable inline.
