# Contexto de Ejecución — US-2.1.11

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc2/US-2.1.11.md` (Issue #52)
- **Fuente Arquitectura:** `CLAUDE.md` — React 19 + TypeScript + Vite (frontend); infraestructura
  de routing/cliente API ya establecida por `US-2.1.8`; backend consumido
  (`POST /preguntas/opcion-multiple`, `POST /preguntas/verdadero-falso`) ya implementado en
  `US-2.1.3`/`US-2.1.4`, sin cambios

## Historia de Usuario
- **ID:** US-2.1.11
- **Título:** Docente carga una pregunta eligiendo su tipo
- **Tipo:** Nueva funcionalidad — frontend puro
- **Puntos:** 3
- **Prioridad:** Alta — reemplaza el placeholder de "+ Nueva pregunta" dejado por `US-2.1.10`,
  siguiente paso de la Iteración 1 antes de `US-2.1.12` (editar) y `US-2.1.13` (eliminar)

## Alcance
Sin cambios de backend — consume `POST /preguntas/opcion-multiple` y
`POST /preguntas/verdadero-falso` tal como quedaron en `US-2.1.3`/`US-2.1.4`. Todo el trabajo
es frontend: pantalla de selección de tipo (`NuevaPreguntaTipo.tsx`) + dos formularios
(`NuevaPreguntaOpcionMultiple.tsx`, `NuevaPreguntaVerdaderoFalso.tsx`), reemplazando el
placeholder de "+ Nueva pregunta" en `router.tsx` bajo
`/materias/:id/banco/preguntas/nueva/*`.

## Adaptación de las fases del skill (frontend puro)
Misma adaptación documentada en `US-1.1.6`/`US-1.1.9`/`US-2.1.8`/`US-2.1.9`/`US-2.1.10`:
Vitest + React Testing Library en vez de pytest-bdd, sin pylint/CC/MI.

| Fase del skill | Adaptación frontend (TypeScript) |
|---|---|
| Fase 1 — BDD | `.feature` Gherkin — 4 escenarios ya definidos en la spec, validados con Vitest (sin step_defs, sin pytest-bdd) |
| Fase 4/5 — Tests | Vitest + React Testing Library (`NuevaPreguntaTipo.tsx`, `NuevaPreguntaOpcionMultiple.tsx`, `NuevaPreguntaVerdaderoFalso.tsx`) |
| Fase 7 — Quality Gates | `npm run lint` (0 errores), `tsc --noEmit` (0 errores), Vitest, cobertura de referencia ≥80% |

## Decisión de componentes UI (a confirmar en Fase 2)
Reutiliza `Button`, `Input`, `Label` (shadcn/ui, ya instalados desde `US-1.1.7`). Selector de
tipo — dos tarjetas clicables, sin componente shadcn nuevo anticipado; formulario de Opción
Múltiple requiere lista dinámica de opciones + radio de correcta (a confirmar en Fase 2 contra
el wireframe `§2.5`).

## Decisiones de Ejecución
- **BDD:** Sí — 4 escenarios ya definidos en la spec (elegir tipo OM, carga exitosa OM, rechazo
  cliente por opciones inválidas, carga exitosa V/F).
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 (4, 5, 7 con la adaptación frontend de la
  tabla de arriba — sin componente backend Python en esta US)

## Perfil Activo
- **Perfil:** clean-architecture-bc (Cognion)
- **Patrón frontend:** React 19 + TypeScript + Vite, sin capas Clean Architecture
- **Umbrales de calidad frontend (adaptados):** ESLint/oxlint 0 errores, `tsc --noEmit` 0
  errores, Vitest — cobertura de referencia ≥80%

## Rutas de Artefactos
- Contexto: `docs/plans/inc2/US-2.1.11-context.md`
- BDD feature: `tests/features/inc2/US-2.1.11-carga-pregunta-tipo.feature`
- Plan: `docs/plans/inc2/US-2.1.11-plan.md`
- Reporte: `docs/reports/inc2/US-2.1.11-report.md`
- Quality report: `quality/reports/inc2/US-2.1.11-quality.json`
