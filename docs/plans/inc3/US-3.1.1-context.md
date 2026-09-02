# Contexto de Ejecución — US-3.1.1

## Fuentes
- **Fuente HU:** `docs/specs/inc3/US-3.1.1.md` (GitHub Issue #145)
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md` (Clean Architecture BC-first), `CLAUDE.md`,
  `docs/design/domain/BC-actividad-evaluativa-modelo.md` §6 (diseño del event store)

## Historia de Usuario
- **ID:** US-3.1.1
- **Título:** Infraestructura de Event Sourcing + CQRS del BC Actividad Evaluativa
- **Tipo:** Infraestructura técnica — sin comando de negocio propio (primer código del BC,
  precondición de `US-3.1.2`/`US-3.1.3` y de toda la Iteración 2 y 3)
- **Puntos:** 5
- **Prioridad:** Alta — bloquea todo el resto del BC Actividad Evaluativa

## Decisiones de Ejecución
- **BDD:** No — decisión explícita de Víctor. La spec ya documenta 4 escenarios Gherkin
  (append/replay, concurrencia optimista, atomicidad, aislamiento entre streams) como
  especificación de comportamiento, pero no se formalizan como `.feature` ejecutable en esta
  US — se valida directamente con tests de integración (Fase 5).
- **skip_bdd:** true
- **Fases a ejecutar:** 0, 2, 3, 4, 5, 7, 8, 9 (se omiten 1 y 6)

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (entities → use_cases → interface_adapters → frameworks, BC-first)
- **Umbrales de calidad:**
  - pylint ≥ 8.0
  - CC ≤ 10
  - MI ≥ 20
  - cobertura ≥ 95%

## Rutas de Artefactos
- Contexto: docs/plans/inc3/US-3.1.1-context.md
- Plan: docs/plans/inc3/US-3.1.1-plan.md
- Reporte: docs/reports/inc3/US-3.1.1-report.md
- Quality report: quality/reports/inc3/US-3.1.1-quality.json
