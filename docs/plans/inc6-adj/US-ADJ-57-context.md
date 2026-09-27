# Contexto de Ejecución — US-ADJ-57

## Fuentes
- **Fuente HU:** `docs/specs/ajustes/US-ADJ-57.md`
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md`, `CLAUDE.md` §"Arquitectura interna" (Clean Architecture BC-first)

## Historia de Usuario
- **ID:** US-ADJ-57
- **Título:** Cada Docente ve y opera solo sobre las materias de sus Comisiones
- **Tipo:** Nueva funcionalidad (autorización — RBAC por asignación Docente↔Comisión, no solo por rol)
- **Puntos:** 8 (cross-cutting, 4 BC: Identidad, Banco de Preguntas, Actividad Evaluativa, Analytics)
- **Prioridad:** Segunda US formal de `Incremento 6-ADJ`, después de `US-ADJ-56`

## Decisiones de Ejecución
- **BDD:** Sí — nueva regla de negocio con criterios de aceptación Gherkin ya definidos en la spec
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
- **Umbrales de calidad:**
  - pylint ≥ 8.0
  - CC ≤ 10
  - MI ≥ 20 (calibrado por incremento, histórico del proyecto > 40)
  - cobertura ≥ umbral vigente en `pyproject.toml`

## Rutas de Artefactos
- Contexto: docs/plans/inc6-adj/US-ADJ-57-context.md
- BDD feature: tests/features/inc6-adj/US-ADJ-57-*.feature
- Plan: docs/plans/inc6-adj/US-ADJ-57-plan.md
- Reporte: docs/reports/inc6-adj/US-ADJ-57-report.md
- Quality report: quality/reports/inc6-adj/US-ADJ-57-quality.json

## Notas específicas de esta US
- **Alcance cruza 4 BC** (Identidad, Banco de Preguntas, Actividad Evaluativa, Analytics) — la
  propia spec pide decidir en Fase 2 si se implementa como una sola US o partida por BC. Dado
  que este skill trabaja una US-IEDD por vez y el Issue #443 ya es el único ticket de GitHub
  para esta regla, se implementa como **una sola US-ADJ-57** con un plan de Fase 2 organizado
  en tandas por BC (Identidad primero, de la que dependen las demás), en un único PR — evita
  fragmentar en 4 Issues/PRs para una regla que es conceptualmente una sola ("ownership de
  Comisión"), y permite testear los 4 BC juntos con los mismos dos Docentes de fixture.
- Riesgo conocido y ya documentado en la spec: CBO en controllers/use cases al sumar la
  consulta de asignación — diseñar la separación desde la Fase 2 (mismo patrón ya visto en
  Incrementos 2 y 6).
- Decisiones de Víctor ya resueltas en la spec: `403` (no `404`) para recursos ajenos;
  actividades de período abierto sin restricción de Comisión las ve/modifica cualquier
  Docente asignado a alguna Comisión de la materia; datos ya existentes no se migran ni se
  borran.
- Sin gate UX (los listados existentes muestran menos elementos, sin pantalla nueva), salvo
  que la Fase 2 detecte un estado vacío nuevo.
