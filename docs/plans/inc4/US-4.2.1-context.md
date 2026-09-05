# Contexto de Ejecución — US-4.2.1

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc4/US-4.2.1.md` (spec IEDD completa, Issue [#240](https://github.com/vvalotto/cognion/issues/240))
- **Fuente Arquitectura:** `CLAUDE.md` (reglas de capas) + `docs/rf/ARQ_v1.md` (ADRs, `ADR-019` RBAC) + `docs/design/domain/BC-analytics-modelo.md` §4

## Historia de Usuario
- **ID:** US-4.2.1
- **Título:** Docente consulta el desempeño de un estudiante elegido
- **Tipo:** Nueva funcionalidad (reutiliza `ObtenerDesempenoEstudianteUseCase` de `US-4.1.2` sin cambios — solo un endpoint/rol nuevo)
- **Puntos:** 2
- **Prioridad:** Alta (bloquea `US-4.2.5`)

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad con criterios de aceptación Gherkin ya redactados en la spec (200 con datos, 200 vacío, 404 estudiante inexistente, 403 rol distinto)
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
- Contexto: docs/plans/inc4/US-4.2.1-context.md
- BDD feature: tests/features/inc4/US-4.2.1-desempeno-estudiante-elegido.feature
- Plan: docs/plans/inc4/US-4.2.1-plan.md
- Reporte: docs/reports/inc4/US-4.2.1-report.md
- Quality report: quality/reports/inc4/US-4.2.1-quality.json
