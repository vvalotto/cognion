# Contexto de Ejecución — US-2.1.13

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc2/US-2.1.13.md` (Issue #54)
- **Fuente Arquitectura:** `CLAUDE.md` — React 19 + TypeScript + Vite (frontend); infraestructura
  de routing/cliente API ya establecida por `US-2.1.8`; backend consumido
  (`DELETE /preguntas/{id}`) ya implementado en `US-2.1.6`, sin cambios

## Historia de Usuario
- **ID:** US-2.1.13
- **Título:** Docente elimina una pregunta desde la UI, con confirmación previa
- **Tipo:** Nueva funcionalidad — frontend puro
- **Puntos:** 2
- **Prioridad:** Alta — reemplaza la acción "Eliminar" deshabilitada en `Banco.tsx` (dejada por
  `US-2.1.10`), cierra la Iteración 1 completa (`US-2.1.10` a `US-2.1.13`)

## Alcance
Sin cambios de backend — consume `DELETE /preguntas/{id}` tal como quedó en `US-2.1.6`. Trabajo
frontend: pantalla `EliminarPregunta.tsx` con confirmación explícita (texto de la pregunta +
aclaración de que es baja lógica, no afecta sesiones pasadas). Necesita poder mostrar el texto
de la pregunta a eliminar — a confirmar en Fase 2 si alcanza con lo que ya devuelve
`GET /bancos/{id}/preguntas` (`US-2.1.7`, consumido por `Banco.tsx`) pasado por navegación, o si
hace falta resolverlo de otra forma. Habilita la acción "Eliminar" en `Banco.tsx`
(deshabilitada desde `US-2.1.10`) y agrega la ruta
`/materias/:materiaId/banco/preguntas/:preguntaId/eliminar` en `router.tsx`.

## Adaptación de las fases del skill (frontend puro)
Misma adaptación documentada en `US-1.1.6`/`US-1.1.9`/`US-2.1.8` a `US-2.1.12`: Vitest + React
Testing Library en vez de pytest-bdd, sin pylint/CC/MI.

| Fase del skill | Adaptación frontend (TypeScript) |
|---|---|
| Fase 1 — BDD | `.feature` Gherkin — 2 escenarios ya definidos en la spec (confirmar/cancelar), validados con Vitest (sin step_defs, sin pytest-bdd) |
| Fase 4/5 — Tests | Vitest + React Testing Library (`EliminarPregunta.tsx`) |
| Fase 7 — Quality Gates | `npm run lint` (0 errores), `tsc --noEmit` (0 errores), Vitest, cobertura de referencia ≥80% |

## Decisiones de Ejecución
- **BDD:** Sí — 2 escenarios ya definidos en la spec (confirmar eliminación, cancelar
  eliminación).
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 (4, 5, 7 con la adaptación frontend de la
  tabla de arriba — sin componente backend Python en esta US)

## Perfil Activo
- **Perfil:** clean-architecture-bc (Cognion)
- **Patrón frontend:** React 19 + TypeScript + Vite, sin capas Clean Architecture
- **Umbrales de calidad frontend (adaptados):** ESLint/oxlint 0 errores, `tsc --noEmit` 0
  errores, Vitest — cobertura de referencia ≥80%

## Rutas de Artefactos
- Contexto: `docs/plans/inc2/US-2.1.13-context.md`
- BDD feature: `tests/features/inc2/US-2.1.13-eliminar-pregunta.feature`
- Plan: `docs/plans/inc2/US-2.1.13-plan.md`
- Reporte: `docs/reports/inc2/US-2.1.13-report.md`
- Quality report: `quality/reports/inc2/US-2.1.13-quality.json`
