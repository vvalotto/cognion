# Contexto de Ejecución — US-2.2.8

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc2/US-2.2.8.md` (Issue #103)
- **Fuente Arquitectura:** `CLAUDE.md` — React 19 + TypeScript + Vite (frontend); backend
  consumido (`PUT /usuarios/me/password`) ya implementado en `US-2.2.5`, sin cambios;
  `docs/design/ux/wireframes-cuentas-administracion.md` §2.5-§2.7
  (`#cambiar-password`, `#cambiar-password-error`, `#cambiar-password-exito`) + prototipo
  `docs/design/ux/prototipos/identidad-cuentas-administracion.html`

## Historia de Usuario
- **ID:** US-2.2.8
- **Título:** Cualquier usuario autenticado cambia su propia contraseña (UI)
- **Tipo:** Nueva funcionalidad — frontend puro
- **Puntos:** 3
- **Prioridad:** Alta — a diferencia del resto de la Iteración 2, accesible a los tres roles,
  no solo Administrador

## Alcance
Sin cambios de backend — consume `PUT /usuarios/me/password` tal como quedó en `US-2.2.5`.
Todo el trabajo es frontend: extiende `cuentas-api.ts` con `cambiarPassword`, pantalla
`frontend/src/pages/CambiarPassword.tsx` (formulario + manejo de error/éxito en la misma
pantalla, sin ruta separada para el estado de error), ruta `/mi-cuenta/cambiar-password` en
`router.tsx` accesible para cualquier rol autenticado (sin `RequireRole`).

## Adaptación de las fases del skill (frontend puro)
Misma adaptación documentada en `US-2.2.6`/`US-2.2.7`: Vitest + React Testing Library en vez
de pytest-bdd, sin pylint/CC/MI.

| Fase del skill | Adaptación frontend (TypeScript) |
|---|---|
| Fase 1 — BDD | `.feature` Gherkin — 3 escenarios ya definidos en la spec, validados con Vitest (sin step_defs, sin pytest-bdd) |
| Fase 4/5 — Tests | Vitest + React Testing Library (`CambiarPassword.tsx`, `cuentas-api.ts`) |
| Fase 7 — Quality Gates | `npm run lint` (oxlint, 0 errores), `tsc --noEmit` (0 errores), Vitest, cobertura de referencia ≥80% |

## Decisión de componentes UI (a confirmar en Fase 2)
Reutiliza `Button`, `Input`, `Label` (shadcn/ui, ya instalados). Sin componente shadcn nuevo
anticipado, a confirmar en Fase 2 contra el wireframe (`§2.5-§2.7`).

## Decisiones de Ejecución
- **BDD:** Sí — 3 escenarios ya definidos en la spec (cambio exitoso, contraseña actual
  incorrecta, bloqueo al tercer fallo).
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 (4, 5, 7 con la adaptación frontend de la
  tabla de arriba — sin componente backend Python en esta US)

## Perfil Activo
- **Perfil:** clean-architecture-bc (Cognion)
- **Patrón frontend:** React 19 + TypeScript + Vite, sin capas Clean Architecture
- **Umbrales de calidad frontend (adaptados):** oxlint 0 errores, `tsc --noEmit` 0 errores,
  Vitest — cobertura de referencia ≥80%

## Rutas de Artefactos
- Contexto: `docs/plans/inc2/US-2.2.8-context.md`
- BDD feature: `tests/features/inc2/US-2.2.8-cambiar-password.feature`
- Plan: `docs/plans/inc2/US-2.2.8-plan.md`
- Reporte: `docs/reports/inc2/US-2.2.8-report.md`
- Quality report: `quality/reports/inc2/US-2.2.8-quality.json`

## Notas de continuidad
- Backend ya existe completo: `PUT /usuarios/me/password` (`US-2.2.5`), incluye
  `intentos_fallidos_password` y bloqueo al tercer fallo (INV-ID-10).
- Reutiliza `apiFetch`/JWT (`US-1.1.6`). Sin `RequireRole` — accesible a cualquier rol
  autenticado, a diferencia de `US-2.2.6`/`US-2.2.7`.
- Comparte el mecanismo de bloqueo con `US-2.2.9` (login refleja cuenta bloqueada), próxima US
  de la iteración — flujos independientes entre sí.
