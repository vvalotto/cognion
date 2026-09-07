# Contexto de Ejecución — US-ADJ-29

## Fuentes
- **Fuente HU:** GitHub Issue [#274](https://github.com/vvalotto/cognion/issues/274) + spec `docs/specs/ajustes/US-ADJ-29.md`
- **Fuente Arquitectura:** `CLAUDE.md` (Clean Architecture BC-first) — esta US es frontend puro, sin capas de dominio

## Historia de Usuario
- **ID:** US-ADJ-29
- **Título:** Home del Estudiante
- **Tipo:** Nueva funcionalidad (pantalla nueva, frontend puro)
- **Puntos:** 2
- **Prioridad:** Alta — resuelve el punto de aterrizaje post-login del Estudiante

## Decisiones de Ejecución
- **BDD:** No — frontend puro sobre rutas ya protegidas, mismo criterio que `US-ADJ-24`/`27`/`28`.
- **skip_bdd:** true
- **Fases a ejecutar:** 0, 2, 3, 4, 5, 7, 8, 9 (se saltan 1 y 6)

## Sin gaps nuevos

Mismo patrón que `US-ADJ-28` (Home del Docente, ya cerrada): saludo genérico ("Hola,
Estudiante"), sin `GET /usuarios/me`. `Inicio.tsx` ya despacha por rol — esta US solo agrega
la rama `estudiante`.

## Perfil Activo
- **Perfil:** clean-architecture-bc — no aplica a esta US (frontend puro)
- **Umbrales de calidad:** gate de frontend del proyecto (`tsc -b`, oxlint, Vitest)

## Rutas de Artefactos
- Contexto: `docs/plans/inc4-adj/US-ADJ-29-context.md`
- BDD feature: no aplica (`skip_bdd: true`)
- Plan: `docs/plans/inc4-adj/US-ADJ-29-plan.md`
- Reporte: `docs/reports/inc4-adj/US-ADJ-29-report.md`
- Quality report: `quality/reports/inc4-adj/US-ADJ-29-quality.json`
