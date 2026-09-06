# Contexto de Ejecución — US-4.1.2

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc4/US-4.1.2.md` (spec IEDD completa, Issue [#233](https://github.com/vvalotto/cognion/issues/233))
- **Fuente Arquitectura:** `CLAUDE.md` (reglas de capas) + `docs/rf/ARQ_v1.md` (ADRs) + `docs/design/domain/BC-analytics-modelo.md` §4/§6

## Historia de Usuario
- **ID:** US-4.1.2
- **Título:** Estudiante consulta su propio desempeño en una materia
- **Tipo:** Nueva funcionalidad
- **Puntos:** 3
- **Prioridad:** Alta (bloquea US-4.1.3 y US-4.2.1)

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad con criterios de aceptación Gherkin ya redactados en la spec (200 con datos, 200 vacío, 401, 403)
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (BC-first: entities → use_cases → interface_adapters → frameworks)
- **Umbrales de calidad:**
  - pylint ≥ 8.0 (default config.json — histórico del proyecto viene cerrando ≥ 9.0)
  - CC ≤ 10
  - MI ≥ (default perfil, ver `config.json` quality_gates.maintainability_index)
  - cobertura ≥ (default perfil — histórico del proyecto cierra en 99-100% en BCs backend)

## Rutas de Artefactos
- Contexto: docs/plans/inc4/US-4.1.2-context.md
- BDD feature: tests/features/inc4/US-4.1.2-desempeno-estudiante.feature
- Plan: docs/plans/inc4/US-4.1.2-plan.md
- Reporte: docs/reports/inc4/US-4.1.2-report.md
- Quality report: quality/reports/inc4/US-4.1.2-quality.json
