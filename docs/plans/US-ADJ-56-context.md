# Contexto de Ejecución — US-ADJ-56

## Fuentes
- **Fuente HU:** `docs/specs/ajustes/US-ADJ-56.md`
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md`, `CLAUDE.md` §"Arquitectura interna" (Clean Architecture BC-first)

## Historia de Usuario
- **ID:** US-ADJ-56
- **Título:** El desempeño del Estudiante incluye las sesiones en vivo
- **Tipo:** Nueva funcionalidad (ampliación de alcance de RF-15/RF-16 al modo en vivo)
- **Puntos:** 5
- **Prioridad:** Alta — Iteración de ajuste `Incremento 6-ADJ`, antes de `BL-011`

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad con criterios de aceptación Gherkin ya definidos en la spec
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
- **Umbrales de calidad:**
  - pylint ≥ 8.0
  - CC ≤ 10
  - MI ≥ 20 (calibrado por incremento, histórico del proyecto > 40)
  - cobertura ≥ umbral vigente en `pyproject.toml`

## Rutas de Artefactos
- Contexto: docs/plans/US-ADJ-56-context.md
- BDD feature: tests/features/inc6-adj/US-ADJ-56-*.feature (mismo criterio que `US-ADJ-58`)
- Plan: docs/plans/US-ADJ-56-plan.md
- Reporte: docs/reports/inc6-adj/US-ADJ-56-report.md
- Quality report: quality/reports/inc6-adj/US-ADJ-56-quality.json

## Notas específicas de esta US
- Puerto nuevo de Analytics hacia Actividad Evaluativa (in-process, `ADR-006`), mismo patrón que `EvaluacionDesempenoConsultaPort` (`US-4.1.1`). Sin eventos ni tablas nuevas.
- Gate UX ya aprobado por Víctor 2026-09-27 (`docs/design/ux/wireframes-analytics.md` §6).
- Backend + frontend juntos (mismo criterio que Analytics Iteración 1/2, sin diferir frontend).
- Cuidar CBO de los controllers existentes de Analytics al ampliar el endpoint (patrón de CRITICAL recurrente documentado en `CLAUDE.md`).
