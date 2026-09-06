# Contexto de Ejecución — US-4.2.6

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc4/US-4.2.6.md` (spec IEDD completa)
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md` + `CLAUDE.md` §Arquitectura interna (Clean Architecture BC-first) — para esta US, frontend puro, aplica la convención de `frontend/src/` ya establecida en US-4.1.3/US-4.2.5

## Historia de Usuario
- **ID:** US-4.2.6
- **Título:** Docente ve "Desempeño por tema"
- **Tipo:** Nueva funcionalidad (frontend)
- **Puntos:** 3
- **Prioridad:** Alta — cierra completa la Iteración 2 del Incremento 4 (RF-17 end-to-end, backend ya cerrado en US-4.2.2/US-4.2.4)

## Decisiones de Ejecución
- **BDD:** No — frontend puro (Vitest + Testing Library), sin backend nuevo ni invariante de dominio que amerite escenarios Gherkin. Mismo criterio ya aplicado a US-4.1.3/US-4.2.5 (frontend-only).
- **skip_bdd:** true
- **Fases a ejecutar:** 0, 2, 3, 4, 8, 9 (se saltan 1, 5, 6 — BDD y tests de integración backend no aplican; Fase 7 se ejecuta con el criterio frontend: oxlint + tsc --noEmit + cobertura Vitest, no pylint/radon)

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (no aplica a esta US — frontend puro, sin capas entities/use_cases/interface_adapters/frameworks)
- **Umbrales de calidad (criterio frontend, mismo que US-4.1.3/US-4.2.5):**
  - oxlint: 0 errores
  - `tsc --noEmit`: 0 errores
  - cobertura Vitest en archivos nuevos: sin umbral numérico fijo del perfil backend — se reporta el % real (histórico del proyecto: 83%-100% en pantallas nuevas)

## Rutas de Artefactos
- Contexto: docs/plans/inc4/US-4.2.6-context.md
- BDD feature: N/A (skip_bdd)
- Plan: docs/plans/inc4/US-4.2.6-plan.md
- Reporte: docs/reports/inc4/US-4.2.6-report.md
- Quality report: quality/reports/inc4/US-4.2.6-quality.json
