# Contexto de Ejecución — US-ADJ-36

## Fuentes
- **Fuente HU:** GitHub Issue [#330](https://github.com/vvalotto/cognion/issues/330) + spec `docs/specs/ajustes/US-ADJ-36.md`
- **Fuente Arquitectura:** `CLAUDE.md` (Clean Architecture BC-first) — perfil `clean-architecture-bc`

## Historia de Usuario
- **ID:** US-ADJ-36
- **Título:** Contraseña segura — política ampliada
- **Tipo:** Mejora de comportamiento existente (invariante de dominio ampliada + cierre de gap real) — backend + frontend
- **Puntos:** 2
- **Prioridad:** Alta — cierra un gap de seguridad real (`CrearUsuario`/`RegistrarEstudiante` sin validación de dominio de contraseña)

## Decisiones de Ejecución
- **BDD:** Sí — cambio de comportamiento de dominio (`INV-ID-11` ampliada) con impacto en 4
  endpoints/comandos, mismo criterio que otras US de invariantes de `Usuario` (`US-2.2.1`,
  `US-2.2.4`, `US-2.2.5`).
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 (todas)

## Fuente de verdad UX
`docs/design/ux/wireframes-identidad-autoservicio.md` §2 (indicador de fortaleza). Prototipo:
`docs/design/ux/prototipos/identidad-autoservicio.html`.

## Depende de
`US-ADJ-35` (ya cerrada, PR #333) — reutiliza el componente `PasswordInput` para el prop
`mostrarFortaleza`.

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (entities → use_cases → interface_adapters → frameworks)
- **Umbrales de calidad:** backend — pylint ≥ 8.0, CC ≤ 10, MI > 20, coverage ≥ 95%
  (`.claude/skills/implement-us/config.json → quality_gates`); frontend — gate del proyecto
  (`tsc -b`, oxlint, Vitest)

## Rutas de Artefactos
- Contexto: `docs/plans/inc5-adj/US-ADJ-36-context.md`
- BDD feature: `tests/features/inc5-adj/US-ADJ-36-contrasena-segura.feature`
- Plan: `docs/plans/inc5-adj/US-ADJ-36-plan.md`
- Reporte: `docs/reports/inc5-adj/US-ADJ-36-report.md`
- Quality report: `quality/reports/inc5-adj/US-ADJ-36-quality.json`
