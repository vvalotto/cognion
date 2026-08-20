# Contexto de Ejecución — US-2.2.7

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc2/US-2.2.7.md` (Issue #102)
- **Fuente Arquitectura:** `CLAUDE.md` — React 19 + TypeScript + Vite (frontend); backend
  consumido (`GET /usuarios/{id}` de `US-2.2.3`, `POST /usuarios/{id}/resetear-password` de
  `US-2.2.4`) ya implementado, sin cambios; `docs/design/ux/wireframes-cuentas-administracion.md`
  §2.2-§2.4 (`#cuenta-detalle`, `#cuenta-resetear`, `#cuenta-reseteada`) + prototipo
  `docs/design/ux/prototipos/identidad-cuentas-administracion.html`

## Historia de Usuario
- **ID:** US-2.2.7
- **Título:** Administrador ve el detalle de una cuenta y resetea/desbloquea (UI)
- **Tipo:** Nueva funcionalidad — frontend puro
- **Puntos:** 3
- **Prioridad:** Alta — segunda US frontend de la Iteración 2, consumida desde el listado de
  `US-2.2.6`

## Alcance
Sin cambios de backend — consume `GET /usuarios/{id}` (`US-2.2.3`) y
`POST /usuarios/{id}/resetear-password` (`US-2.2.4`) tal como quedaron. Todo el trabajo es
frontend: cliente API extendido (`cuentas-api.ts`, agrega `obtenerCuenta`/`resetearPassword`),
tres pantallas nuevas (`CuentaDetalle.tsx`, `ResetearPassword.tsx`, `CuentaReseteada.tsx`),
tres rutas nuevas en `router.tsx` protegidas con `RequireRole rol="administrador"`. Agrupa tres
pantallas del wireframe en un único flujo de US, mismo criterio que `US-2.1.11`.

## Adaptación de las fases del skill (frontend puro)
Misma adaptación documentada en `US-2.1.9`/`US-2.1.10`/`US-2.2.6`: Vitest + React Testing
Library en vez de pytest-bdd, sin pylint/CC/MI.

| Fase del skill | Adaptación frontend (TypeScript) |
|---|---|
| Fase 1 — BDD | `.feature` Gherkin — 3 escenarios ya definidos en la spec, validados con Vitest (sin step_defs, sin pytest-bdd) |
| Fase 4/5 — Tests | Vitest + React Testing Library (`CuentaDetalle.tsx`, `ResetearPassword.tsx`, `CuentaReseteada.tsx`, `cuentas-api.ts`) |
| Fase 7 — Quality Gates | `npm run lint` (oxlint, 0 errores), `tsc --noEmit` (0 errores), Vitest, cobertura de referencia ≥80% |

## Decisión de componentes UI (a confirmar en Fase 2)
Reutiliza `Button`, `Input`, `Label` (shadcn/ui, ya instalados). Alerta de bloqueo — a
confirmar en Fase 2 contra el wireframe (`§2.2`): componente `Alert` de shadcn/ui si ya está
instalado, o markup simple con Tailwind si no.

## Decisiones de Ejecución
- **BDD:** Sí — 3 escenarios ya definidos en la spec (ver detalle de cuenta bloqueada, resetear
  contraseña exitosamente, cancelar el reseteo).
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 (4, 5, 7 con la adaptación frontend de la
  tabla de arriba — sin componente backend Python en esta US)

## Perfil Activo
- **Perfil:** clean-architecture-bc (Cognion)
- **Patrón frontend:** React 19 + TypeScript + Vite, sin capas Clean Architecture
- **Umbrales de calidad frontend (adaptados):** oxlint 0 errores, `tsc --noEmit` 0 errores,
  Vitest — cobertura de referencia ≥80%

## Rutas de Artefactos
- Contexto: `docs/plans/inc2/US-2.2.7-context.md`
- BDD feature: `tests/features/inc2/US-2.2.7-detalle-cuenta-reseteo.feature`
- Plan: `docs/plans/inc2/US-2.2.7-plan.md`
- Reporte: `docs/reports/inc2/US-2.2.7-report.md`
- Quality report: `quality/reports/inc2/US-2.2.7-quality.json`

## Notas de continuidad
- Backend ya existe completo: `GET /usuarios/{id}` (`US-2.2.3`),
  `POST /usuarios/{id}/resetear-password` (`US-2.2.4`).
- Reutiliza `apiFetch`/JWT (`US-1.1.6`) y el guard `RequireRole` (`US-1.1.9`).
- Se navega hacia acá desde una fila del listado de `US-2.2.6` (`/cuentas` → `/cuentas/:id`).
- Sigue `US-2.2.8` (cambio de contraseña propio, UI) y `US-2.2.9` (login refleja bloqueo, UI).
