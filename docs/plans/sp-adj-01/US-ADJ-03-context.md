# Contexto de Ejecución — US-ADJ-03

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-03.md` (Issue #116)
- **Fuente Arquitectura:** `CLAUDE.md` — Clean Architecture BC-first (perfil
  `clean-architecture-bc`), FastAPI + SQLAlchemy async + PostgreSQL (backend) y React 19 +
  TypeScript + Vite (frontend). Extiende `US-2.1.7` (`GET /bancos/{id}/preguntas`) y
  `US-2.1.10` (`Banco.tsx`), ya implementadas.

## Historia de Usuario
- **ID:** US-ADJ-03
- **Título:** Paginar el listado del banco de preguntas
- **Tipo:** Nueva funcionalidad (backend + frontend)
- **Puntos:** 5
- **Prioridad:** Segunda US de la iteración de ajuste conjunta `SP-ADJ-01`, después de
  `US-ADJ-01`. `US-ADJ-05` (paginación de cuentas) depende de esta para reusar su
  componente `Pagination` frontend.

## Alcance
Backend: agrega `fecha_creacion: datetime` a `PreguntaPlantillaOpcionMultiple`/
`PreguntaPlantillaVerdaderoFalso` (fijado una sola vez al crear, inmutable en `editar()`),
migración Alembic con backfill (timestamp único de la migración para preguntas existentes),
`PreguntaRepositoryPort.filtrar()` gana `pagina`/`tamanio_pagina` y retorna
`(preguntas, total)`, `ORDER BY fecha_creacion, id` (desempate estable) en el gateway,
`GET /bancos/{id}/preguntas` acepta los query params nuevos. Frontend: `Banco.tsx` agrega
estado de página y controles de paginación (componente nuevo `Pagination`, reusable por
`US-ADJ-05`), reset a página 1 al cambiar cualquier filtro. **Gate UX previo obligatorio**:
`docs/design/ux/wireframes-banco-preguntas.md` no contempla paginación — se actualiza en
Fase 2 antes de tocar `frontend/`.

## Adaptación de las fases del skill
US mixta backend+frontend — a diferencia de `US-ADJ-01` (frontend puro), **sí** aplican
pylint/CC/MI/coverage sobre el componente backend (`src/banco_preguntas/`), con la
adaptación frontend ya documentada en USs previas para la parte de `Banco.tsx`.

| Fase del skill | Adaptación |
|---|---|
| Fase 1 — BDD | `.feature` Gherkin (4 escenarios ya definidos en la spec) — steps reales con `pytest-bdd` para el backend; validación del frontend con Vitest (sin pytest-bdd), mismo criterio que USs frontend previas |
| Fase 2 — Plan | Incluye la actualización de `wireframes-banco-preguntas.md` como tarea previa a cualquier cambio de `frontend/` |
| Fase 4/5 — Tests | pytest (unit + integración) para backend; Vitest + RTL para `Banco.tsx` |
| Fase 7 — Quality Gates | Backend: pylint ≥ 8.0, CC ≤ 10, MI ≥ 20 (umbrales de perfil), coverage ≥ 95% (calibrado del Incremento, ver `US-2.2.5-quality.json`). Frontend: oxlint 0 errores, `tsc --noEmit` 0 errores, cobertura de referencia ≥80% |

## Decisiones de Ejecución
- **BDD:** Sí — 4 escenarios ya definidos en la spec (más de una página, cambiar de página,
  filtro reinicia paginación, una sola página).
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc (Cognion)
- **Patrón arquitectónico (backend):** Clean Architecture BC-first — entities → use_cases →
  interface_adapters → frameworks
- **Patrón frontend:** React 19 + TypeScript + Vite, sin capas Clean Architecture
- **Umbrales de calidad backend:**
  - pylint ≥ 8.0
  - CC ≤ 10
  - MI ≥ 20
  - cobertura ≥ 95% (calibrado del Incremento 2, no el 90% default del perfil)
- **Umbrales de calidad frontend (adaptados):** ESLint/oxlint 0 errores, `tsc --noEmit` 0
  errores, Vitest — cobertura de referencia ≥80%

## Rutas de Artefactos
- Contexto: `docs/plans/sp-adj-01/US-ADJ-03-context.md`
- BDD feature: `tests/features/sp-adj-01/US-ADJ-03-paginar-banco-preguntas.feature`
- Plan: `docs/plans/sp-adj-01/US-ADJ-03-plan.md`
- Reporte: `docs/reports/sp-adj-01/US-ADJ-03-report.md`
- Quality report: `quality/reports/sp-adj-01/US-ADJ-03-quality.json`
