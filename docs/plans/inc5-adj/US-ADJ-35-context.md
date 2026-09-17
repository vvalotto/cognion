# Contexto de Ejecución — US-ADJ-35

## Fuentes
- **Fuente HU:** GitHub Issue [#329](https://github.com/vvalotto/cognion/issues/329) + spec `docs/specs/ajustes/US-ADJ-35.md`
- **Fuente Arquitectura:** `CLAUDE.md` (Clean Architecture BC-first) — esta US es frontend puro, sin capas de dominio

## Historia de Usuario
- **ID:** US-ADJ-35
- **Título:** Toggle mostrar/ocultar contraseña
- **Tipo:** Nueva funcionalidad (componente compartido nuevo, frontend puro)
- **Puntos:** 1
- **Prioridad:** Alta — primera US de la Iteración 1, `US-ADJ-36` depende de su componente `PasswordInput`

## Decisiones de Ejecución
- **BDD:** No — frontend puro, componente de presentación sin lógica de negocio, mismo
  criterio que `US-ADJ-24`/`27`/`28`/`29`/`30`.
- **skip_bdd:** true
- **Fases a ejecutar:** 0, 2, 3, 4, 5, 7, 8, 9 (se saltan 1 y 6)

## Fuente de verdad UX
`docs/design/ux/wireframes-identidad-autoservicio.md` §2. Prototipo:
`docs/design/ux/prototipos/identidad-autoservicio.html`.

## Perfil Activo
- **Perfil:** clean-architecture-bc — no aplica a esta US (frontend puro)
- **Umbrales de calidad:** gate de frontend del proyecto (`tsc -b`, oxlint, Vitest)

## Rutas de Artefactos
- Contexto: `docs/plans/inc5-adj/US-ADJ-35-context.md`
- BDD feature: no aplica (`skip_bdd: true`)
- Plan: `docs/plans/inc5-adj/US-ADJ-35-plan.md`
- Reporte: `docs/reports/inc5-adj/US-ADJ-35-report.md`
- Quality report: `quality/reports/inc5-adj/US-ADJ-35-quality.json`
