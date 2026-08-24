# Contexto de Ejecución — US-1.1.0

## Fuentes
- **Fuente HU:** `docs/specs/inc1/US-1.1.0.md` (Issue GitHub #5)
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md` + `CLAUDE.md` (Clean Architecture BC-first)

## Historia de Usuario
- **ID:** US-1.1.0
- **Título:** Administrador da de alta cuentas de usuario, crea una comisión y asigna docentes
- **Tipo:** Nueva funcionalidad
- **Puntos:** 5
- **Prioridad:** Alta — precondición de toda la Iteración 1 (BC Identidad)

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad con criterios de aceptación Gherkin ya definidos en la spec
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (entities → use_cases → interface_adapters → frameworks, BC-first)
- **Umbrales de calidad:**
  - pylint ≥ 8.0
  - CC ≤ 10
  - MI ≥ 20
  - cobertura ≥ 95%

## Rutas de Artefactos
- Contexto: docs/plans/inc1/US-1.1.0-context.md
- BDD feature: tests/features/inc1/US-1.1.0-alta-usuarios-comision-docentes.feature
- Plan: docs/plans/inc1/US-1.1.0-plan.md
- Reporte: docs/reports/inc1/US-1.1.0-report.md
- Quality report: quality/reports/inc1/US-1.1.0-quality.json
