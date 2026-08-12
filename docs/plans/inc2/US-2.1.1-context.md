# Contexto de Ejecución — US-2.1.1

## Fuentes
- **Fuente HU:** `docs/specs/inc2/US-2.1.1.md`
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md` (Clean Architecture BC-first)

## Historia de Usuario
- **ID:** US-2.1.1
- **Título:** Docente da de alta una materia y su banco de preguntas
- **Tipo:** Nueva funcionalidad
- **Puntos:** 3
- **Prioridad:** Alta — precondición de toda la Iteración 1 del Incremento 2 (US-2.1.2 a
  US-2.1.7 dependen de que existan `Materia`/`Banco`)

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad con criterios de aceptación Gherkin ya definidos en la
  spec (`docs/specs/inc2/US-2.1.1.md`); se formalizan como `.feature` en Fase 1 y se validan
  con step_defs de pytest-bdd en Fase 6.
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
- Contexto: docs/plans/inc2/US-2.1.1-context.md
- BDD feature: tests/features/inc2/US-2.1.1-alta-materia-banco.feature
- Plan: docs/plans/inc2/US-2.1.1-plan.md
- Reporte: docs/reports/inc2/US-2.1.1-report.md
- Quality report: quality/reports/inc2/US-2.1.1-quality.json
