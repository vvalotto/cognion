# Contexto de Ejecución — US-3.4.5

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc3/US-3.4.5.md`
- **Fuente Arquitectura:** Documento local — `CLAUDE.md` (§Arquitectura interna) + `docs/rf/ARQ_v1.md` + `.claude/skills/implement-us/customizations/clean-architecture-bc.json`

## Historia de Usuario
- **ID:** US-3.4.5
- **Título:** Estudiante ve sus materias y las actividades disponibles
- **Tipo:** Nueva funcionalidad (backend + frontend)
- **Puntos:** 5
- **Prioridad:** Alta — primer punto de entrada del Estudiante al frontend de Actividad Evaluativa (Iteración 4, Incremento 3)

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad con criterios de aceptación Gherkin ya redactados en la spec
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (BC-first: entities → use_cases → interface_adapters → frameworks)
- **Umbrales de calidad:**
  - pylint ≥ 8.0
  - CC ≤ 10
  - MI ≥ 20
  - cobertura ≥ 95.0%
  - CBO ≤ 10 (DesignReviewer, pre-push — `pyproject.toml` `[tool.designreviewer]`)

## Rutas de Artefactos
- Contexto: docs/plans/inc3/US-3.4.5-context.md
- BDD feature: tests/features/inc3/US-3.4.5-mis-materias-actividades.feature
- Plan: docs/plans/inc3/US-3.4.5-plan.md
- Reporte: docs/reports/inc3/US-3.4.5-report.md
- Quality report: quality/reports/inc3/US-3.4.5-quality.json
