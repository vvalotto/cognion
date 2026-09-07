# Contexto de Ejecución — US-ADJ-30

## Fuentes
- **Fuente HU:** GitHub Issue [#275](https://github.com/vvalotto/cognion/issues/275) + spec `docs/specs/ajustes/US-ADJ-30.md`
- **Fuente Arquitectura:** `CLAUDE.md` (Clean Architecture BC-first) — esta US es frontend puro, sin capas de dominio

## Historia de Usuario
- **ID:** US-ADJ-30
- **Título:** Home del Administrador
- **Tipo:** Nueva funcionalidad (pantalla nueva, frontend puro)
- **Puntos:** 2
- **Prioridad:** Alta — última US de la Iteración 1b, la cierra completa

## Decisiones de Ejecución
- **BDD:** No — frontend puro sobre rutas ya protegidas, mismo criterio que `US-ADJ-24`/`27`/`28`/`29`.
- **skip_bdd:** true
- **Fases a ejecutar:** 0, 2, 3, 4, 5, 7, 8, 9 (se saltan 1 y 6)

## Sin gaps nuevos

Mismo patrón que `US-ADJ-28`/`29`: saludo genérico ("Hola, Administrador"), sin
`GET /usuarios/me`. Único elemento adicional respecto de las otras 2 homes: el Administrador
nunca pasó por `/` (login lo mandaba directo a `/docentes/nuevo`) — `Login.tsx` también se
ajusta en esta US (`RUTA_POST_LOGIN.administrador` → `"/"`).

## Perfil Activo
- **Perfil:** clean-architecture-bc — no aplica a esta US (frontend puro)
- **Umbrales de calidad:** gate de frontend del proyecto (`tsc -b`, oxlint, Vitest)

## Rutas de Artefactos
- Contexto: `docs/plans/inc4-adj/US-ADJ-30-context.md`
- BDD feature: no aplica (`skip_bdd: true`)
- Plan: `docs/plans/inc4-adj/US-ADJ-30-plan.md`
- Reporte: `docs/reports/inc4-adj/US-ADJ-30-report.md`
- Quality report: `quality/reports/inc4-adj/US-ADJ-30-quality.json`
