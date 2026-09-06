# Contexto de Ejecución — US-4.2.2

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc4/US-4.2.2.md`
- **Fuente Arquitectura:** Documento local — `docs/rf/ARQ_v1.md` + `CLAUDE.md` (sección "Arquitectura interna")

## Historia de Usuario
- **ID:** US-4.2.2
- **Título:** ComisionConsultaPort — comisiones por materia y estudiantes por comisión
- **Tipo:** Nueva funcionalidad (técnica — puerto de consulta cross-BC nuevo de punta a punta)
- **Puntos:** 3
- **Prioridad:** Alta — desbloquea US-4.2.4 (tasa de error por tema) y US-4.2.5 (pantalla docente)

## Decisiones de Ejecución
- **BDD:** Sí — la spec ya trae escenarios Gherkin completos (6 escenarios, incluido el consumo in-process desde Analytics)
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
- Contexto: docs/plans/inc4/US-4.2.2-context.md
- BDD feature: tests/features/inc4/US-4.2.2-comision-query-port.feature
- Plan: docs/plans/inc4/US-4.2.2-plan.md
- Reporte: docs/reports/inc4/US-4.2.2-report.md
- Quality report: quality/reports/inc4/US-4.2.2-quality.json
