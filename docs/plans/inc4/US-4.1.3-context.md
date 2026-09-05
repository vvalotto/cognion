# Contexto de Ejecución — US-4.1.3

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc4/US-4.1.3.md` (Issue [#234](https://github.com/vvalotto/cognion/issues/234))
- **Fuente Arquitectura:** `CLAUDE.md` — React 19 + TypeScript + Vite (frontend); infraestructura
  de routing/cliente API ya establecida (`US-1.1.6`); backend consumido
  (`GET /analytics/materias/{materia_id}/mi-desempeno`) ya implementado en `US-4.1.2`, sin
  cambios; selector de materia reutiliza `listarMisMaterias()` (`identidad-estudiante-api.ts`,
  `US-3.4.5`), sin endpoint nuevo

## Historia de Usuario
- **ID:** US-4.1.3
- **Título:** Estudiante ve la pantalla "Mi desempeño"
- **Tipo:** Nueva funcionalidad — frontend puro
- **Puntos:** 3
- **Prioridad:** Alta — cierra completa la Iteración 1 del Incremento 4 (RF-15)

## Alcance
Sin cambios de backend — consume `GET /analytics/materias/{materia_id}/mi-desempeno`
(`US-4.1.2`) tal cual quedó, y `listarMisMaterias()` (`US-3.4.5`) para el selector de materia.
Trabajo frontend: cliente API nuevo `analytics-api.ts` (`obtenerMiDesempeno(materiaId)`),
pantalla `MiDesempeno.tsx` (`#est-desempeno`: selector de materia condicional — oculto si el
estudiante cursa una sola materia, mismo criterio que el resto de selectores de una sola
opción del proyecto —, `.summary-bar` de resumen acumulado, lista de `.eval-item` por
evaluación, estado vacío, error genérico), y ruta nueva `/analytics/mi-desempeno` protegida con
`RequireRole rol="estudiante"`.

## Adaptación de las fases del skill (frontend puro)
Misma adaptación documentada en `US-1.1.6`/`US-2.1.8` a `US-2.1.13`/`US-3.4.x`: Vitest + React
Testing Library en vez de pytest-bdd, sin pylint/CC/MI.

| Fase del skill | Adaptación frontend (TypeScript) |
|---|---|
| Fase 1 — BDD | `.feature` Gherkin — 4 escenarios ya definidos en la spec (una materia con datos, selector con más de una materia, estado vacío, acceso sin rol estudiante), validados con Vitest (sin step_defs, sin pytest-bdd) |
| Fase 4/5 — Tests | Vitest + React Testing Library (`MiDesempeno.tsx`, `analytics-api.ts`) |
| Fase 7 — Quality Gates | `npm run lint` (0 errores), `tsc --noEmit` (0 errores), Vitest, cobertura de referencia ≥80% |

## Decisiones de Ejecución
- **BDD:** Sí — 4 escenarios ya definidos en la spec (una sola materia, más de una materia,
  materia sin evaluaciones finalizadas, acceso sin rol estudiante).
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 (4, 5, 7 con la adaptación frontend de la
  tabla de arriba — sin componente backend Python en esta US)

## Perfil Activo
- **Perfil:** clean-architecture-bc (Cognion)
- **Patrón frontend:** React 19 + TypeScript + Vite, sin capas Clean Architecture
- **Umbrales de calidad frontend (adaptados):** ESLint/oxlint 0 errores, `tsc --noEmit` 0
  errores, Vitest — cobertura de referencia ≥80%

## Rutas de Artefactos
- Contexto: `docs/plans/inc4/US-4.1.3-context.md`
- BDD feature: `tests/features/inc4/US-4.1.3-mi-desempeno.feature`
- Plan: `docs/plans/inc4/US-4.1.3-plan.md`
- Reporte: `docs/reports/inc4/US-4.1.3-report.md`
- Quality report: `quality/reports/inc4/US-4.1.3-quality.json`
