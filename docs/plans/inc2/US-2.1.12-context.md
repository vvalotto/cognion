# Contexto de Ejecución — US-2.1.12

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc2/US-2.1.12.md` (Issue #53)
- **Fuente Arquitectura:** `CLAUDE.md` — React 19 + TypeScript + Vite (frontend); infraestructura
  de routing/cliente API ya establecida por `US-2.1.8`; formularios de `US-2.1.11`
  (`NuevaPreguntaOpcionMultiple.tsx`, `NuevaPreguntaVerdaderoFalso.tsx`) reutilizados en modo
  edición; backend consumido (`PUT /preguntas/{id}`) ya implementado en `US-2.1.5`, sin cambios

## Historia de Usuario
- **ID:** US-2.1.12
- **Título:** Docente edita una pregunta existente desde la UI
- **Tipo:** Nueva funcionalidad — frontend puro
- **Puntos:** 3
- **Prioridad:** Alta — reemplaza el placeholder de "Editar" dejado por `US-2.1.10`, siguiente
  paso de la Iteración 1 antes de `US-2.1.13` (eliminar)

## Alcance
Sin cambios de backend — consume `PUT /preguntas/{id}` tal como quedó en `US-2.1.5`. Trabajo
frontend: pantalla `EditarPregunta.tsx` que reutiliza los formularios de `US-2.1.11` según el
tipo concreto de la pregunta, prellenados con sus valores actuales (necesita poder obtener la
pregunta a editar — a confirmar en Fase 2 si alcanza con lo que ya devuelve
`GET /bancos/{id}/preguntas` de `US-2.1.7`, consumido por `Banco.tsx` en `US-2.1.10`, o si hace
falta un método nuevo en el cliente API). Reemplaza el placeholder de "Editar" en `router.tsx`
bajo `/materias/:materiaId/banco/preguntas/:preguntaId/editar`. El tipo de la pregunta no es
editable (mismo criterio que el backend, `US-2.1.5`).

## Adaptación de las fases del skill (frontend puro)
Misma adaptación documentada en `US-1.1.6`/`US-1.1.9`/`US-2.1.8`/`US-2.1.9`/`US-2.1.10`/
`US-2.1.11`: Vitest + React Testing Library en vez de pytest-bdd, sin pylint/CC/MI.

| Fase del skill | Adaptación frontend (TypeScript) |
|---|---|
| Fase 1 — BDD | `.feature` Gherkin — 2 escenarios ya definidos en la spec, validados con Vitest (sin step_defs, sin pytest-bdd) |
| Fase 4/5 — Tests | Vitest + React Testing Library (`EditarPregunta.tsx`) |
| Fase 7 — Quality Gates | `npm run lint` (0 errores), `tsc --noEmit` (0 errores), Vitest, cobertura de referencia ≥80% |

## Decisión de componentes UI (a confirmar en Fase 2)
Reutiliza los formularios de `US-2.1.11` (`NuevaPreguntaOpcionMultiple.tsx`,
`NuevaPreguntaVerdaderoFalso.tsx`) — a confirmar en Fase 2 si se extraen a modo compartido
(prop `modo: "crear" | "editar"` + valores iniciales) o si `EditarPregunta.tsx` es un wrapper
que los invoca prellenados.

## Decisiones de Ejecución
- **BDD:** Sí — 2 escenarios ya definidos en la spec (edición exitosa, rechazo de cliente por
  opciones inválidas).
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 (4, 5, 7 con la adaptación frontend de la
  tabla de arriba — sin componente backend Python en esta US)

## Perfil Activo
- **Perfil:** clean-architecture-bc (Cognion)
- **Patrón frontend:** React 19 + TypeScript + Vite, sin capas Clean Architecture
- **Umbrales de calidad frontend (adaptados):** ESLint/oxlint 0 errores, `tsc --noEmit` 0
  errores, Vitest — cobertura de referencia ≥80%

## Rutas de Artefactos
- Contexto: `docs/plans/inc2/US-2.1.12-context.md`
- BDD feature: `tests/features/inc2/US-2.1.12-editar-pregunta.feature`
- Plan: `docs/plans/inc2/US-2.1.12-plan.md`
- Reporte: `docs/reports/inc2/US-2.1.12-report.md`
- Quality report: `quality/reports/inc2/US-2.1.12-quality.json`
