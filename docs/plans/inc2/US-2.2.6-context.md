# Contexto de Ejecución — US-2.2.6

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc2/US-2.2.6.md` (Issue #101)
- **Fuente Arquitectura:** `CLAUDE.md` — React 19 + TypeScript + Vite (frontend); backend
  consumido (`GET /usuarios?rol=&estado=&busqueda=`) ya implementado en `US-2.2.2`, sin
  cambios; `docs/design/ux/wireframes-cuentas-administracion.md` §2.1 (`#cuentas`) + prototipo
  `docs/design/ux/prototipos/identidad-cuentas-administracion.html`

## Historia de Usuario
- **ID:** US-2.2.6
- **Título:** Administrador ve y filtra el listado de cuentas (UI)
- **Tipo:** Nueva funcionalidad — frontend puro
- **Puntos:** 3
- **Prioridad:** Alta — primera US frontend de la Iteración 2, punto de entrada al detalle de
  cuenta (`US-2.2.7`)

## Alcance
Sin cambios de backend — consume `GET /usuarios?rol=&estado=&busqueda=` tal como quedó en
`US-2.2.2`. Todo el trabajo es frontend: cliente API tipado nuevo (`cuentas-api.ts`), tabla +
filtros en `frontend/src/pages/Cuentas.tsx`, ruta `/cuentas` nueva en `router.tsx` protegida
con `RequireRole rol="administrador"`.

## Adaptación de las fases del skill (frontend puro)
Misma adaptación documentada en `US-2.1.9`/`US-2.1.10` (parte frontend): Vitest + React
Testing Library en vez de pytest-bdd, sin pylint/CC/MI.

| Fase del skill | Adaptación frontend (TypeScript) |
|---|---|
| Fase 1 — BDD | `.feature` Gherkin — 2 escenarios ya definidos en la spec, validados con Vitest (sin step_defs, sin pytest-bdd) |
| Fase 4/5 — Tests | Vitest + React Testing Library (`Cuentas.tsx`, `cuentas-api.ts`) |
| Fase 7 — Quality Gates | `npm run lint` (oxlint, 0 errores), `tsc --noEmit` (0 errores), Vitest, cobertura de referencia ≥80% |

## Decisión de componentes UI (a confirmar en Fase 2)
Reutiliza `Button`, `Input`, `Label`, `Select` (shadcn/ui, ya instalados desde `US-1.1.7`/
`US-2.1.10`). Tabla — sin componente shadcn nuevo anticipado, a confirmar en Fase 2 contra el
wireframe (`§2.1`).

## Decisiones de Ejecución
- **BDD:** Sí — 2 escenarios ya definidos en la spec (filtrar por rol y estado, navegar al
  detalle).
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 (4, 5, 7 con la adaptación frontend de la
  tabla de arriba — sin componente backend Python en esta US)

## Perfil Activo
- **Perfil:** clean-architecture-bc (Cognion)
- **Patrón frontend:** React 19 + TypeScript + Vite, sin capas Clean Architecture
- **Umbrales de calidad frontend (adaptados):** oxlint 0 errores, `tsc --noEmit` 0 errores,
  Vitest — cobertura de referencia ≥80%

## Rutas de Artefactos
- Contexto: `docs/plans/inc2/US-2.2.6-context.md`
- BDD feature: `tests/features/inc2/US-2.2.6-listado-filtro-cuentas.feature`
- Plan: `docs/plans/inc2/US-2.2.6-plan.md`
- Reporte: `docs/reports/inc2/US-2.2.6-report.md`
- Quality report: `quality/reports/inc2/US-2.2.6-quality.json`

## Notas de continuidad
- Backend ya existe completo: `GET /usuarios?rol=&estado=&busqueda=` (`US-2.2.2`).
- Reutiliza `apiFetch`/JWT (`US-1.1.6`) y el guard `RequireRole` (`US-1.1.9`).
- De acá se navega al detalle de cuenta, que implementa `US-2.2.7` (siguiente US) — el click
  de fila debe dejar lista la ruta `/cuentas/:usuarioId`, aunque el detalle en sí sea
  placeholder hasta esa US (mismo patrón usado en `US-2.1.8`→`US-2.1.9`/`.10`).
