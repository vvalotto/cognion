# Contexto de Ejecución — US-3.2.1

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc3/US-3.2.1.md`
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md` + `CLAUDE.md` §"Arquitectura interna — reglas no negociables" + perfil `clean-architecture-bc`

## Historia de Usuario
- **ID:** US-3.2.1
- **Título:** Estudiante confirma una respuesta (persistencia atómica)
- **Tipo:** Nueva funcionalidad
- **Puntos:** 5
- **Prioridad:** Alta — abre la Iteración 2 del Incremento 3, bloquea US-3.2.2/US-3.2.3/US-3.2.4

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad con criterios de aceptación Gherkin ya redactados en la spec
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
- Contexto: docs/plans/inc3/US-3.2.1-context.md
- BDD feature: tests/features/inc3/US-3.2.1-registrar-respuesta.feature
- Plan: docs/plans/inc3/US-3.2.1-plan.md
- Reporte: docs/reports/inc3/US-3.2.1-report.md
- Quality report: quality/reports/inc3/US-3.2.1-quality.json
