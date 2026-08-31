# Contexto de Ejecución — US-3.4.7

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc3/US-3.4.7.md`
- **Fuente Arquitectura:** Documento local — `docs/rf/ARQ_v1.md` + `CLAUDE.md` (reglas de capas, ADRs 001-019)

## Historia de Usuario
- **ID:** US-3.4.7
- **Título:** Estudiante finaliza su evaluación y ve la revisión completa
- **Tipo:** Nueva funcionalidad (frontend puro — nueva pantalla de revisión)
- **Puntos:** 3
- **Prioridad:** Alta — Iteración 4 del Incremento 3, cierra el lado Estudiante

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad visible de extremo a extremo (finalizar, ver revisión, acceso posterior desde el listado), con criterios de aceptación Gherkin ya redactados en la spec.
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
- Contexto: docs/plans/inc3/US-3.4.7-context.md
- BDD feature: tests/features/inc3/US-3.4.7-finalizar-revision.feature
- Plan: docs/plans/inc3/US-3.4.7-plan.md
- Reporte: docs/reports/inc3/US-3.4.7-report.md
- Quality report: quality/reports/inc3/US-3.4.7-quality.json

## Notas específicas de esta US
- No requiere decisión arquitectónica (spec §Impacto arquitectónico) — consume dos endpoints
  ya existentes sin cambios: `POST /evaluaciones/{id}/finalizar` y
  `GET /evaluaciones/{id}/revision` (ambos de `US-3.2.3`).
- Backend: sin cambios.
- Frontend: `RevisionEvaluacion.tsx` (resumen + detalle por pregunta), ruta nueva
  `/mis-actividades/:actividadId/revision` en `router.tsx`. Consume también la navegación de
  entrada desde `RendirEvaluacion.tsx` (`US-3.4.6`, botón "Finalizar") y desde el listado de
  actividades (`Badge` "Finalizada — ver revisión", `US-3.4.5`).
- Gate UX: `docs/design/ux/wireframes-actividad-evaluativa.md` §3.5 (`#est-revision`) ya
  aprobado — no requiere nuevo ciclo de prototipo.
