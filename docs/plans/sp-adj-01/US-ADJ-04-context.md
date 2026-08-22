# Contexto de Ejecución — US-ADJ-04

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-04.md` (Issue #114)
- **Fuente Arquitectura:** `CLAUDE.md` — React 19 + TypeScript + Vite (frontend); primitivas
  `Card`/`CardContent`/`Badge`/`Breadcrumb`/`Button variant="destructive-solid"` ya creadas
  por `US-ADJ-01`, a reutilizar sin modificar su comportamiento existente. Prototipo aprobado
  `docs/design/ux/prototipos/identidad-cuentas-administracion.html` y
  `docs/design/ux/wireframes-cuentas-administracion.md` como fuente de verdad UX.

## Historia de Usuario
- **ID:** US-ADJ-04
- **Título:** Alinear visualmente las pantallas de Cuentas/Contraseñas con el prototipo
  aprobado
- **Tipo:** Refactorización de presentación (sin cambio de comportamiento) — frontend puro
- **Puntos:** 3
- **Prioridad:** Tercera US de la iteración de ajuste conjunta `SP-ADJ-01`, después de
  `US-ADJ-01` (de la que reutiliza primitivas) y `US-ADJ-03` (sin dependencia directa entre
  ambas, implementada después por orden secuencial de nombre de US).

## Alcance
Sin cambios de backend, sin cambios de dominio, sin nuevos endpoints ni componentes nuevos en
`components/ui/` — solo variantes nuevas de `Badge` (`rol-*`/`estado-*`). Trabajo frontend:
aplicar `Card`/`Badge`/`Breadcrumb`/`destructive-solid` a 5 pantallas existentes de Cuentas/
Contraseñas (`Cuentas.tsx`, `CuentaDetalle.tsx`, `ResetearPassword.tsx`,
`CuentaReseteada.tsx`, `CambiarPassword.tsx`). `Login.tsx`/`LoginCuentaBloqueadaError.tsx`
quedan fuera de alcance — ya siguen su propio prototipo aprobado (Identidad, Incremento 1).

## Adaptación de las fases del skill (frontend puro)
Misma adaptación que `US-ADJ-01`: Vitest + React Testing Library en vez de pytest-bdd, sin
pylint/CC/MI.

| Fase del skill | Adaptación frontend (TypeScript) |
|---|---|
| Fase 1 — BDD | `.feature` Gherkin — 4 escenarios ya definidos en la spec, validados con Vitest (sin step_defs, sin pytest-bdd) |
| Fase 4/5 — Tests | Vitest + React Testing Library, ajustando selectors que dependan de estructura DOM que cambie |
| Fase 6 — BDD | Verificación funcional vía Vitest + comparación visual manual en navegador real contra el prototipo — mismo criterio explícito que `US-ADJ-01` |
| Fase 7 — Quality Gates | `npm run lint` (oxlint, 0 errores), `tsc --noEmit` (0 errores), Vitest, cobertura de referencia ≥80% |

## Decisiones de Ejecución
- **BDD:** Sí — 4 escenarios ya definidos en la spec (listado con tags y acción "Ver",
  detalle con tarjeta de datos, confirmación de reseteo como pantalla de éxito, sin
  regresión funcional).
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc (Cognion)
- **Patrón frontend:** React 19 + TypeScript + Vite, sin capas Clean Architecture
- **Umbrales de calidad frontend (adaptados):** ESLint/oxlint 0 errores, `tsc --noEmit` 0
  errores, Vitest — cobertura de referencia ≥80%

## Rutas de Artefactos
- Contexto: `docs/plans/sp-adj-01/US-ADJ-04-context.md`
- BDD feature: `tests/features/sp-adj-01/US-ADJ-04-estilo-visual-cuentas.feature`
- Plan: `docs/plans/sp-adj-01/US-ADJ-04-plan.md`
- Reporte: `docs/reports/sp-adj-01/US-ADJ-04-report.md`
- Quality report: `quality/reports/sp-adj-01/US-ADJ-04-quality.json`
