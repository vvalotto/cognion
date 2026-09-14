# Contexto de Ejecución — US-ADJ-44

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-44.md` (mismo criterio que todas
  las US-ADJ del proyecto, `docs/plans/inc5-adj/inc5-adj-candidatas.md` §Iteración 4)
- **Fuente Arquitectura:** Documento local — `CLAUDE.md` §"Arquitectura interna" +
  `docs/rf/ARQ_v1.md` + `docs/design/domain/BC-analytics-modelo.md` §8

## Historia de Usuario
- **ID:** US-ADJ-44
- **Título:** Docente consulta el desempeño de una Comisión completa
- **Tipo:** Nueva funcionalidad
- **Puntos:** 5 (sin asignación formal — mismo criterio que el resto de Analytics,
  `docs/traceability/matrix.md`)
- **Prioridad:** Alta — primera US de la Iteración 4 del Incremento 5-ADJ

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad de negocio con criterios de aceptación Gherkin ya
  redactados en la spec.
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
- Contexto: docs/plans/US-ADJ-44-context.md
- BDD feature: tests/features/inc5-adj/US-ADJ-44-desempeno-por-comision.feature
- Plan: docs/plans/US-ADJ-44-plan.md
- Reporte: docs/reports/inc5-adj/US-ADJ-44-report.md
- Quality report: quality/reports/inc5-adj/US-ADJ-44-quality.json

## Notas específicas de esta US
- BC principal: Analytics (sin aggregate propio, solo lectura vía puertos).
- Toca también BC Actividad Evaluativa: amplía el guard de rol de
  `GET /evaluaciones/{evaluacion_id}/revision` (hoy exclusivo de `require_estudiante`) para
  admitir también `require_docente`, sin verificación de pertenencia Docente↔Materia (mismo
  precedente de RBAC por rol ya usado en `US-4.2.1`).
- Primer método de `EvaluacionDesempenoConsultaPort` que lee `ActividadEvaluativaPeriodoAbierto`
  (no solo el stream de `Evaluacion`) — ya anticipado en `BC-analytics-modelo.md` §8.2.
