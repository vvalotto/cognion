# Contexto de Ejecución — US-2.1.10

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc2/US-2.1.10.md` (Issue #51)
- **Fuente Arquitectura:** `CLAUDE.md` — React 19 + TypeScript + Vite (frontend); infraestructura
  de routing/cliente API ya establecida por `US-2.1.8`; backend consumido (`GET
  /bancos/{id}/preguntas?filtros`) ya implementado en `US-2.1.7`, sin cambios

## Historia de Usuario
- **ID:** US-2.1.10
- **Título:** Docente ve y filtra el banco de preguntas de una materia
- **Tipo:** Nueva funcionalidad — frontend puro
- **Puntos:** 3
- **Prioridad:** Alta — punto de entrada a cargar/editar/eliminar preguntas (`US-2.1.11` a
  `US-2.1.13`), bloqueada hasta ahora por no tener pantalla de navegación de materias
  (resuelta en `US-2.1.9`)

## Alcance
Sin cambios de backend — consume `GET /bancos/{id}/preguntas` tal como quedó en `US-2.1.7`.
Todo el trabajo es frontend: tabla + barra de filtros en `frontend/src/pages/Banco.tsx`,
reemplazando el placeholder de `US-2.1.8` en `router.tsx` para la ruta `/materias/:id/banco`.

## Adaptación de las fases del skill (frontend puro)
Misma adaptación documentada en `US-1.1.6`/`US-1.1.9`/`US-2.1.8`/`US-2.1.9` (parte frontend):
Vitest + React Testing Library en vez de pytest-bdd, sin pylint/CC/MI.

| Fase del skill | Adaptación frontend (TypeScript) |
|---|---|
| Fase 1 — BDD | `.feature` Gherkin — 3 escenarios ya definidos en la spec, validados con Vitest (sin step_defs, sin pytest-bdd) |
| Fase 4/5 — Tests | Vitest + React Testing Library (`Banco.tsx`, cliente API si requiere extensión) |
| Fase 7 — Quality Gates | `npm run lint` (0 errores), `tsc --noEmit` (0 errores), Vitest, cobertura de referencia ≥80% |

## Decisión de componentes UI (a confirmar en Fase 2)
Reutiliza `Button`, `Input`, `Label` (shadcn/ui, ya instalados desde `US-1.1.7`). Tabla y
filtros — sin componente shadcn nuevo anticipado (posible `Select` para dificultad/importancia
si no está ya instalado), a confirmar en Fase 2 contra el wireframe (`§2.3`).

## Decisiones de Ejecución
- **BDD:** Sí — 3 escenarios ya definidos en la spec (ver banco sin filtros, filtrar por
  dificultad, filtro sin resultados).
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 (4, 5, 7 con la adaptación frontend de la
  tabla de arriba — sin componente backend Python en esta US)

## Perfil Activo
- **Perfil:** clean-architecture-bc (Cognion)
- **Patrón frontend:** React 19 + TypeScript + Vite, sin capas Clean Architecture
- **Umbrales de calidad frontend (adaptados):** ESLint/oxlint 0 errores, `tsc --noEmit` 0
  errores, Vitest — cobertura de referencia ≥80%

## Rutas de Artefactos
- Contexto: `docs/plans/inc2/US-2.1.10-context.md`
- BDD feature: `tests/features/inc2/US-2.1.10-listado-filtro-banco.feature`
- Plan: `docs/plans/inc2/US-2.1.10-plan.md`
- Reporte: `docs/reports/inc2/US-2.1.10-report.md`
- Quality report: `quality/reports/inc2/US-2.1.10-quality.json`
