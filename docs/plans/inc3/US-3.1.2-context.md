# Contexto de Ejecución — US-3.1.2

## Fuentes
- **Fuente HU:** Documento local `docs/specs/inc3/US-3.1.2.md`
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md` + `CLAUDE.md` (reglas de capas) + perfil `clean-architecture-bc`

## Historia de Usuario
- **ID:** US-3.1.2
- **Título:** Docente crea una actividad de período abierto
- **Tipo:** Nueva funcionalidad
- **Puntos:** 5
- **Prioridad:** Alta — bloquea US-3.1.3 y toda la Iteración 1

## Decisiones de Ejecución
- **BDD:** Sí — la spec ya trae 5 escenarios Gherkin (creación válida + 4 rechazos) formalizables como `.feature`
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (BC-first: entities → use_cases → interface_adapters → frameworks)
- **Umbrales de calidad:**
  - pylint ≥ 8.0
  - CC ≤ 10
  - MI ≥ 20
  - cobertura ≥ 95%

## Rutas de Artefactos
- Contexto: docs/plans/inc3/US-3.1.2-context.md
- BDD feature: tests/features/inc3/US-3.1.2-crear-actividad-periodo-abierto.feature
- Plan: docs/plans/inc3/US-3.1.2-plan.md
- Reporte: docs/reports/inc3/US-3.1.2-report.md
- Quality report: quality/reports/inc3/US-3.1.2-quality.json
