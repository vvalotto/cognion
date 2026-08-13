# Contexto de Ejecución — US-2.1.7

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc2/US-2.1.7.md` (Issue #48)
- **Fuente Arquitectura:** `CLAUDE.md` + `docs/rf/ARQ_v1.md` (Clean Architecture BC-first)

## Historia de Usuario
- **ID:** US-2.1.7
- **Título:** Docente filtra el banco por materia, unidad, tema, dificultad e importancia
- **Tipo:** Nueva funcionalidad (query pura, sin comando ni evento de dominio)
- **Puntos:** 3
- **Prioridad:** Última US backend de la Iteración 1 (Incremento 2)

## Decisiones de Ejecución
- **BDD:** Sí — la spec ya define 3 escenarios Gherkin (filtro combinado, sin filtros, sin resultados)
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (entities → use_cases → interface_adapters → frameworks, BC-first)
- **Umbrales de calidad (pyproject.toml):**
  - pylint ≥ 8.0
  - CC ≤ 10
  - CBO ≤ 10 (DesignReviewer, `[tool.designreviewer]`)
  - MI ≥ 20 (default de perfil — sin override en pyproject.toml)
  - cobertura ≥ 95%

## Rutas de Artefactos
- Contexto: docs/plans/inc2/US-2.1.7-context.md
- BDD feature: tests/features/inc2/US-2.1.7-filtrar-banco.feature
- Plan: docs/plans/inc2/US-2.1.7-plan.md
- Reporte: docs/reports/inc2/US-2.1.7-report.md
- Quality report: quality/reports/inc2/US-2.1.7-quality.json

## Notas de continuidad (patrones detectados en US previas de la iteración)
- **CRITICAL de CBO en `PreguntasController`:** reapareció en US-2.1.2, US-2.1.5 y US-2.1.6 al
  sumar cada nuevo use case inyectado. `US-2.1.7` suma `FiltrarBancoUseCase` — vigilar CBO en
  el pre-push gate; si reaparece, aplicar el mismo criterio ya usado (tipar el evento/resultado
  de retorno como `object` en el controller) antes de considerar partir el controller.
- Query pura sin evento de dominio — no aplica el patrón command/event de `US-2.1.3`–`.6`.
