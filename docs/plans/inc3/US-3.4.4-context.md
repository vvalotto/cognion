# Contexto de Ejecución — US-3.4.4

## Fuentes
- **Fuente HU:** docs/specs/inc3/US-3.4.4.md
- **Fuente Arquitectura:** CLAUDE.md + docs/rf/ARQ_v1.md (Clean Architecture BC-first)

## Historia de Usuario
- **ID:** US-3.4.4
- **Título:** Docente ve el detalle de una actividad, extiende el plazo y la cierra manualmente
- **Tipo:** Nueva funcionalidad (backend: nuevo endpoint de consulta; frontend: 3 pantallas nuevas)
- **Puntos:** 5
- **Prioridad:** Alta — Iteración 4 del Incremento 3 (RF-11b)

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad visible al usuario (detalle, extensión de plazo, cierre manual)
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (BC-first) — extiende `ActividadQueryPort` (US-3.4.2), reutiliza `PATCH /actividades/{id}/periodo` (US-3.3.1) y `POST /actividades/{id}/cerrar` (US-3.3.2) sin cambios; agrega `GET /actividades/{id}`
- **Umbrales de calidad:**
  - Backend: pylint ≥ 8.0, CC ≤ 10, MI ≥ 20, cobertura ≥ 95%
  - Frontend: oxlint 0 errores, `tsc --noEmit` 0 errores, cobertura Vitest de las pantallas nuevas (criterio ya usado en US-2.1.8 a US-3.4.3)

## Rutas de Artefactos
- Contexto: docs/plans/inc3/US-3.4.4-context.md
- BDD feature: tests/features/inc3/US-3.4.4-detalle-actividad.feature
- Plan: docs/plans/inc3/US-3.4.4-plan.md
- Reporte: docs/reports/inc3/US-3.4.4-report.md
- Quality report: quality/reports/inc3/US-3.4.4-quality.json
