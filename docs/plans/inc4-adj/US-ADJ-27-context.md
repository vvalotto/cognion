# Contexto de Ejecución — US-ADJ-27

## Fuentes
- **Fuente HU:** GitHub Issue [#272](https://github.com/vvalotto/cognion/issues/272) + spec `docs/specs/ajustes/US-ADJ-27.md`
- **Fuente Arquitectura:** `CLAUDE.md` (Clean Architecture BC-first, perfil `clean-architecture-bc`) — esta US es frontend puro, sin capas de dominio

## Historia de Usuario
- **ID:** US-ADJ-27
- **Título:** Menú de navegación persistente en AppLayout
- **Tipo:** Nueva funcionalidad (componente de navegación nuevo, frontend puro)
- **Puntos:** 2
- **Prioridad:** Alta — primera US de la Iteración 1b, gate para `US-ADJ-28`/`29`/`30`

## Decisiones de Ejecución
- **BDD:** No — frontend puro sobre rutas ya protegidas por `RequireRole` (`US-1.1.9`), sin
  comportamiento de dominio ni backend nuevo. Mismo criterio que otras US de frontend puro
  del proyecto (`US-ADJ-24`, `US-2.1.10`, `US-3.4.2`).
- **skip_bdd:** true
- **Fases a ejecutar:** 0, 2, 3, 4, 5, 7, 8, 9 (se saltan 1 y 6). Fase 4 = tests de
  componente (`AppNav.test.tsx`); Fase 5 = tests de integración a nivel router
  (`router.test.tsx` o `AppLayout.test.tsx`, mismo patrón que `US-ADJ-24`).

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** Clean Architecture BC-first (entities/use_cases/interface_adapters/frameworks) — no aplica a esta US (frontend puro)
- **Umbrales de calidad:** no aplican umbrales de pylint/CC/MI/coverage backend — se usa el
  gate de frontend del proyecto (`tsc -b` sin errores, `oxlint` sin errores, cobertura de
  branches del proyecto ≥ 80% global)

## Rutas de Artefactos
- Contexto: `docs/plans/inc4-adj/US-ADJ-27-context.md`
- BDD feature: no aplica (`skip_bdd: true`)
- Plan: `docs/plans/inc4-adj/US-ADJ-27-plan.md`
- Reporte: `docs/reports/inc4-adj/US-ADJ-27-report.md`
- Quality report: `quality/reports/inc4-adj/US-ADJ-27-quality.json`
