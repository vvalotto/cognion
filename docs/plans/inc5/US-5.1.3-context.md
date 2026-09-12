# Contexto de Ejecución — US-5.1.3

## Fuentes
- **Fuente HU:** `docs/specs/inc5/US-5.1.3.md`
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md` + ADRs (`docs/adr/`) + `CLAUDE.md`

## Historia de Usuario
- **ID:** US-5.1.3
- **Título:** Notificación de cierre manual de una Actividad Evaluativa de período abierto
- **Tipo:** Nueva funcionalidad
- **Puntos:** 3
- **Prioridad:** Cierra completa la Iteración 1 del Incremento 5

## Decisiones de Ejecución
- **BDD:** Sí — mismo criterio que US-5.1.2; la spec ya trae 4 escenarios Gherkin listos.
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (BC-first: entities → use_cases → interface_adapters → frameworks)
- **Umbrales de calidad:**
  - pylint ≥ 8.0
  - CC ≤ 10
  - MI ≥ (según perfil, ver quality_gates de config.json)
  - cobertura ≥ (según perfil, ver quality_gates de config.json)

## Rutas de Artefactos
- Contexto: docs/plans/inc5/US-5.1.3-context.md
- BDD feature: tests/features/inc5/US-5.1.3-notificacion-cierre-actividad.feature
- Plan: docs/plans/inc5/US-5.1.3-plan.md
- Reporte: docs/reports/inc5/US-5.1.3-report.md
- Quality report: quality/reports/inc5/US-5.1.3-quality.json
