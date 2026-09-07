# Contexto de Ejecución — US-ADJ-28

## Fuentes
- **Fuente HU:** GitHub Issue [#273](https://github.com/vvalotto/cognion/issues/273) + spec `docs/specs/ajustes/US-ADJ-28.md`
- **Fuente Arquitectura:** `CLAUDE.md` (Clean Architecture BC-first) — esta US es frontend puro, sin capas de dominio

## Historia de Usuario
- **ID:** US-ADJ-28
- **Título:** Home del Docente
- **Tipo:** Nueva funcionalidad (pantalla nueva, frontend puro)
- **Puntos:** 2
- **Prioridad:** Alta — resuelve el punto de aterrizaje post-login del Docente

## Decisiones de Ejecución
- **BDD:** No — frontend puro sobre rutas ya protegidas, mismo criterio que `US-ADJ-24`/`27`.
- **skip_bdd:** true
- **Fases a ejecutar:** 0, 2, 3, 4, 5, 7, 8, 9 (se saltan 1 y 6)

## Gap detectado en Fase 0 (decidido con Víctor antes de escribir la spec)

El wireframe (§2.1) pide "Hola, {nombre}" — ningún endpoint expone el nombre del propio
usuario autenticado (`GET /usuarios/{id}` es solo `administrador`; JWT solo trae `sub`/`rol`).
Decisión: saludo genérico ("Hola, Docente"), sin agregar `GET /usuarios/me`. Desvío del
wireframe literal, documentado en la spec. Misma decisión aplica a `US-ADJ-29`/`30`.

## Perfil Activo
- **Perfil:** clean-architecture-bc — no aplica a esta US (frontend puro)
- **Umbrales de calidad:** gate de frontend del proyecto (`tsc -b`, oxlint, Vitest) — sin
  umbrales de pylint/CC/MI/coverage backend

## Rutas de Artefactos
- Contexto: `docs/plans/inc4-adj/US-ADJ-28-context.md`
- BDD feature: no aplica (`skip_bdd: true`)
- Plan: `docs/plans/inc4-adj/US-ADJ-28-plan.md`
- Reporte: `docs/reports/inc4-adj/US-ADJ-28-report.md`
- Quality report: `quality/reports/inc4-adj/US-ADJ-28-quality.json`
