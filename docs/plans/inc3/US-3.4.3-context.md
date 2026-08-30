# Contexto de Ejecución — US-3.4.3

## Fuentes
- **Fuente HU:** docs/specs/inc3/US-3.4.3.md
- **Fuente Arquitectura:** CLAUDE.md + docs/rf/ARQ_v1.md (Clean Architecture BC-first)

## Historia de Usuario
- **ID:** US-3.4.3
- **Título:** Docente crea una nueva actividad de período abierto
- **Tipo:** Nueva funcionalidad (frontend puro, sin cambios de backend)
- **Puntos:** 3
- **Prioridad:** Alta — Iteración 4 del Incremento 3 (RF-11)

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad visible al usuario (formulario de creación de actividad)
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (BC-first) — esta US no toca `src/`, solo `frontend/`
- **Umbrales de calidad:**
  - Backend: pylint ≥ 8.0, CC ≤ 10, MI ≥ 20, cobertura ≥ 95% (no aplica — sin cambios de backend)
  - Frontend: oxlint 0 errores, `tsc --noEmit` 0 errores, cobertura Vitest de las pantallas nuevas (criterio ya usado en US-2.1.8 a US-3.4.2)

## Rutas de Artefactos
- Contexto: docs/plans/inc3/US-3.4.3-context.md
- BDD feature: tests/features/inc3/US-3.4.3-nueva-actividad.feature
- Plan: docs/plans/inc3/US-3.4.3-plan.md
- Reporte: docs/reports/inc3/US-3.4.3-report.md
- Quality report: quality/reports/inc3/US-3.4.3-quality.json
