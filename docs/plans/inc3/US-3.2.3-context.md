# Contexto de Ejecución — US-3.2.3

## Fuentes
- **Fuente HU:** GitHub Issue [#158](https://github.com/vvalotto/cognion/issues/158)
- **Fuente Arquitectura:** `CLAUDE.md` + `docs/design/domain/BC-actividad-evaluativa-modelo.md`

## Historia de Usuario
- **ID:** US-3.2.3
- **Título:** Estudiante finaliza su evaluación y ve la revisión completa
- **Tipo:** Nueva funcionalidad
- **Puntos:** 5
- **Prioridad:** Alta — cierra el ciclo de vida de `Evaluacion` y habilita RF-13

## Decisiones de Ejecución
- **BDD:** Sí — mismo patrón que `US-3.2.1`/`US-3.2.2` (comandos de dominio + query sobre un
  aggregate con invariantes de transición de estado)
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (entities → use_cases → interface_adapters → frameworks, BC-first)
- **Umbrales de calidad:**
  - pylint ≥ 8.0 (histórico del BC: ≥ 9.2)
  - CC ≤ 10
  - MI ≥ 20 (histórico del BC: ≥ 45)
  - cobertura ≥ 95%
  - CBO ≤ 10 (`[tool.designreviewer]`, pre-push gate — bloquea si CRITICAL)

## Rutas de Artefactos
- Contexto: docs/plans/inc3/US-3.2.3-context.md
- BDD feature: tests/features/inc3/US-3.2.3-finalizar-evaluacion-revision.feature
- Plan: docs/plans/inc3/US-3.2.3-plan.md
- Reporte: docs/reports/inc3/US-3.2.3-report.md
- Quality report: quality/reports/inc3/US-3.2.3-quality.json
- Spec de negocio: docs/specs/inc3/US-3.2.3.md
