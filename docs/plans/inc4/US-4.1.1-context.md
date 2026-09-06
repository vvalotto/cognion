# Contexto de Ejecución — US-4.1.1

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc4/US-4.1.1.md`
- **Fuente Arquitectura:** Documento local — `docs/rf/ARQ_v1.md` + `CLAUDE.md` (perfil `clean-architecture-bc`)

## Historia de Usuario
- **ID:** US-4.1.1
- **Título:** Infraestructura de consulta del BC Analytics
- **Tipo:** Nueva funcionalidad (primer código real del BC, técnica — sin comando/query de negocio propio)
- **Puntos:** 5
- **Prioridad:** Alta — bloquea el resto de la Iteración 1 y 2 de Analytics (orden de implementación fijado en `docs/plans/inc4/inc4-candidatas.md`)

## Decisiones de Ejecución
- **BDD:** Sí — la US tiene criterios de aceptación en Gherkin ya redactados en la spec (5 escenarios), comportamiento observable (algoritmo de consulta sobre el event store).
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (entities → use_cases → interface_adapters → frameworks, BC-first)
- **Umbrales de calidad:**
  - pylint ≥ 8.0 (default config.json — sin override específico en el perfil; histórico del proyecto viene cerrando ≥ 9.0)
  - CC ≤ 10
  - MI ≥ (default perfil, ver `config.json` quality_gates.maintainability_index)
  - cobertura ≥ (default perfil — histórico del proyecto cierra en 99-100% en BCs backend)

## Rutas de Artefactos
- Contexto: docs/plans/inc4/US-4.1.1-context.md
- BDD feature: tests/features/inc4/US-4.1.1-infra-consulta-analytics.feature
- Plan: docs/plans/inc4/US-4.1.1-plan.md
- Reporte: docs/reports/inc4/US-4.1.1-report.md
- Quality report: quality/reports/inc4/US-4.1.1-quality.json
