# Contexto de Ejecución — US-2.1.9

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc2/US-2.1.9.md` (Issue #50, alcance ampliado
  2026-08-14 tras el gap detectado en `US-2.1.8`)
- **Fuente Arquitectura:** `CLAUDE.md` — Clean Architecture BC-first (backend,
  `src/banco_preguntas/`) + React 19 + TypeScript + Vite (frontend); infraestructura de
  routing/cliente API ya establecida por `US-2.1.8`

## Historia de Usuario
- **ID:** US-2.1.9
- **Título:** Docente ve el listado de materias y da de alta una nueva
- **Tipo:** Nueva funcionalidad — backend + frontend
- **Puntos:** 5 (ampliado desde la estimación original de 3, por el alcance backend agregado)
- **Prioridad:** Alta — bloquea `US-2.1.10` (necesita al menos una materia con banco para
  listar/filtrar), primera US de la Iteración 1 que reintroduce cambios de `src/` desde
  `US-2.1.7`

## Alcance backend agregado (gap de US-2.1.8)
El backend no exponía `GET /materias`. Se agrega en esta US siguiendo el patrón Clean
Architecture BC-first ya establecido (`entities/ports` → `use_cases` → `interface_adapters` →
`frameworks`), mismo orden obligatorio del perfil `clean-architecture-bc`:
- `MateriaRepositoryPort.listar()` (nuevo)
- `BancoRepositoryPort.obtener_por_materia_id()` (nuevo)
- `ListarMateriasUseCase` — orquesta materia + banco + conteo de preguntas activas,
  reutilizando `PreguntaRepositoryPort.filtrar()` (no se agrega método nuevo a ese puerto)
- `GET /materias` en `materias_router.py`, rol `docente`

## Adaptación de las fases del skill — parte backend (Python) vs. frontend (TypeScript)
Esta US es mixta. La parte backend sigue el perfil `clean-architecture-bc` sin adaptación
(pylint/CC/MI/coverage vía pytest). La parte frontend usa la adaptación ya documentada en
`US-1.1.6`/`US-1.1.9`/`US-2.1.8` (Vitest en vez de pytest-bdd, sin pylint/CC/MI).

| Fase del skill | Backend (Python) | Frontend (TypeScript) |
|---|---|---|
| Fase 1 — BDD | `.feature` Gherkin único para toda la US — escenarios backend validados con pytest-bdd, escenarios frontend validados con Vitest (sin step_defs) |
| Fase 4/5 — Tests | pytest (unitarios de use case/gateway, integración de API con PostgreSQL real) | Vitest + React Testing Library (`banco-preguntas-api.ts`, `Materias.tsx`, `NuevaMateria.tsx`) |
| Fase 7 — Quality Gates | pylint/CC/MI/coverage (umbrales del perfil activo) | `npm run lint` (0 errores), `tsc --noEmit` (0 errores), Vitest, cobertura ≥80% de referencia |

## Decisión de componentes UI (a confirmar en Fase 2)
Reutiliza `Button`, `Input`, `Label` (shadcn/ui, ya instalados desde `US-1.1.7`). Grilla de
materias con tarjetas — sin componente shadcn nuevo anticipado, a confirmar en Fase 2 contra
el wireframe (`§2.1`, `§2.2`).

## Decisiones de Ejecución
- **BDD:** Sí — 4 escenarios ya definidos en la spec (ver listado, alta exitosa, rechazo por
  nombre duplicado, conteo de preguntas activas en `GET /materias`).
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 (4, 5, 7 con parte backend Python sin
  adaptar y parte frontend adaptada, ver tabla)

## Perfil Activo
- **Perfil:** clean-architecture-bc (Cognion)
- **Patrón arquitectónico backend:** Clean Architecture BC-first — orden obligatorio
  entities/ports → use_cases → interface_adapters → frameworks
- **Patrón frontend:** React 19 + TypeScript + Vite, sin capas Clean Architecture
- **Umbrales de calidad backend:** pylint ≥ 8.0, CC ≤ 10, MI > 20, coverage ≥ 95% (leídos del
  perfil activo, `.claude/skills/implement-us/config.json` → `clean-architecture-bc.json`)
- **Umbrales de calidad frontend (adaptados):** ESLint/oxlint 0 errores, `tsc --noEmit` 0
  errores, Vitest — cobertura de referencia ≥80%

## Rutas de Artefactos
- Contexto: `docs/plans/inc2/US-2.1.9-context.md`
- BDD feature: `tests/features/inc2/US-2.1.9-listado-alta-materias.feature`
- Plan: `docs/plans/inc2/US-2.1.9-plan.md`
- Reporte: `docs/reports/inc2/US-2.1.9-report.md`
- Quality report: `quality/reports/inc2/US-2.1.9-quality.json`
