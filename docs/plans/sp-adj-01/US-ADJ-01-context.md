# Contexto de Ejecución — US-ADJ-01

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-01.md` (Issue #112)
- **Fuente Arquitectura:** `CLAUDE.md` — React 19 + TypeScript + Vite (frontend); prototipo
  aprobado `docs/design/ux/prototipos/banco-preguntas-carga-filtrado.html` y
  `docs/design/ux/wireframes-banco-preguntas.md` como fuente de verdad UX (sin cambios de
  diseño, solo aplicación al código existente); componentes base (`button.tsx`/`input.tsx`/
  `label.tsx`, shadcn) ya establecidos por Identidad (`US-1.1.6`/`US-1.1.9`)

## Historia de Usuario
- **ID:** US-ADJ-01
- **Título:** Alinear visualmente las pantallas de Banco de Preguntas con el prototipo aprobado
- **Tipo:** Refactorización de presentación (sin cambio de comportamiento) — frontend puro
- **Puntos:** 3
- **Prioridad:** Primera US de la iteración de ajuste conjunta (SP-ADJ-01), antes de US-ADJ-03
  — establece el lenguaje visual (`Card`, `Badge`, `Breadcrumb`) que US-ADJ-03 reutiliza para
  sus controles de paginación

## Alcance
Sin cambios de backend, sin cambios de dominio, sin nuevos endpoints. Trabajo frontend: 3
componentes nuevos en `frontend/src/components/ui/` (`Card`, `Badge`) y
`frontend/src/components/` (`Breadcrumb`), aplicados a 8 pantallas existentes de Banco de
Preguntas (`Materias.tsx`, `NuevaMateria.tsx`, `Banco.tsx`, `NuevaPreguntaTipo.tsx`,
`NuevaPreguntaOpcionMultiple.tsx`, `NuevaPreguntaVerdaderoFalso.tsx`, `EditarPregunta.tsx`,
`EliminarPregunta.tsx`). Ningún criterio de aceptación funcional de `US-2.1.9` a `US-2.1.13`
cambia — mismos endpoints, mismas validaciones, mismas rutas.

## Adaptación de las fases del skill (frontend puro)
Misma adaptación documentada en `US-1.1.6`/`US-1.1.9`/`US-2.1.8` a `US-2.1.13`: Vitest + React
Testing Library en vez de pytest-bdd, sin pylint/CC/MI.

| Fase del skill | Adaptación frontend (TypeScript) |
|---|---|
| Fase 1 — BDD | `.feature` Gherkin — 3 escenarios ya definidos en la spec (listado de materias, banco con tags de color, sin regresión funcional), validados con Vitest (sin step_defs, sin pytest-bdd) |
| Fase 4/5 — Tests | Vitest + React Testing Library, ajustando selectors que dependan de estructura DOM que cambie |
| Fase 6 — BDD | Verificación funcional de los 3 escenarios vía Vitest + **comparación visual manual en navegador real contra el prototipo** (requisito explícito de la spec — no alcanza con lectura de código ni con tests automatizados de estilo) |
| Fase 7 — Quality Gates | `npm run lint` (oxlint, 0 errores), `tsc --noEmit` (0 errores), Vitest, cobertura de referencia ≥80% |

## Decisiones de Ejecución
- **BDD:** Sí — 3 escenarios ya definidos en la spec (cards de materias, tags de color del
  banco, sin regresión funcional).
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 (4, 5, 6, 7 con la adaptación frontend de
  la tabla de arriba — sin componente backend Python en esta US)

## Perfil Activo
- **Perfil:** clean-architecture-bc (Cognion)
- **Patrón frontend:** React 19 + TypeScript + Vite, sin capas Clean Architecture
- **Umbrales de calidad frontend (adaptados):** ESLint/oxlint 0 errores, `tsc --noEmit` 0
  errores, Vitest — cobertura de referencia ≥80%

## Rutas de Artefactos
- Contexto: `docs/plans/sp-adj-01/US-ADJ-01-context.md`
- BDD feature: `tests/features/sp-adj-01/US-ADJ-01-estilo-visual-banco.feature`
- Plan: `docs/plans/sp-adj-01/US-ADJ-01-plan.md`
- Reporte: `docs/reports/sp-adj-01/US-ADJ-01-report.md`
- Quality report: `quality/reports/sp-adj-01/US-ADJ-01-quality.json`
