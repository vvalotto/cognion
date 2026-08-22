# Contexto de Ejecución — US-ADJ-05

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-05.md` (Issue #115)
- **Fuente Arquitectura:** `CLAUDE.md` — Clean Architecture BC-first (perfil
  `clean-architecture-bc`), FastAPI + SQLAlchemy async + PostgreSQL (backend, BC Identidad) y
  React 19 + TypeScript + Vite (frontend). Extiende `US-2.2.2` (`GET /usuarios`) y
  `US-2.2.6` (`Cuentas.tsx`), ya implementadas. Reutiliza `frontend/src/components/ui/pagination.tsx`
  (introducido por `US-ADJ-03`) sin duplicarlo — dependencia explícita ya cumplida (mergeada).

## Historia de Usuario
- **ID:** US-ADJ-05
- **Título:** Paginar el listado de cuentas
- **Tipo:** Nueva funcionalidad (backend + frontend)
- **Puntos:** 4
- **Prioridad:** Última US de la iteración de ajuste conjunta `SP-ADJ-01`, después de
  `US-ADJ-03` (de la que depende para reusar `Pagination`) y `US-ADJ-04` (mismas pantallas,
  ya con el estilo visual aplicado).

## Alcance
Backend: `CuentaQueryPort.listar()` gana `pagina`/`tamanio_pagina` opcionales (mismo criterio
opt-in que `US-ADJ-03`: si el caller no los manda, devuelve todas las cuentas que matchean
los filtros — no hay otro caller de `listar()` además de `ListarCuentasUseCase`, pero se
mantiene el mismo patrón por consistencia), retorno pasa a incluir `total`. **Sin migración**:
`Usuario.creado_en` ya existe desde `US-2.2.3`, se usa directamente como criterio de orden
estable (`ORDER BY creado_en, id`). Frontend: `Cuentas.tsx` agrega estado de página, reset a
1 al cambiar cualquier filtro, reusa `<Pagination>` ya existente.

## Adaptación de las fases del skill
US mixta backend+frontend, mismo criterio que `US-ADJ-03`.

| Fase del skill | Adaptación |
|---|---|
| Fase 1 — BDD | `.feature` Gherkin (4 escenarios, mismo patrón que `US-ADJ-03`) — steps reales con `pytest-bdd` para el backend; validación del frontend con Vitest |
| Fase 4/5 — Tests | pytest (unit + integración) para backend; Vitest + RTL para `Cuentas.tsx` |
| Fase 7 — Quality Gates | Backend: pylint ≥ 8.0, CC ≤ 10, MI ≥ 20, coverage ≥ 95% (calibrado del Incremento). Frontend: oxlint 0 errores, `tsc --noEmit` 0 errores, cobertura de referencia ≥80% |

## Decisiones de Ejecución
- **BDD:** Sí — 4 escenarios ya definidos en la spec (más de una página, cambiar de página,
  filtro reinicia paginación, una sola página).
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc (Cognion)
- **Patrón arquitectónico (backend):** Clean Architecture BC-first — entities → use_cases →
  interface_adapters → frameworks (BC Identidad)
- **Patrón frontend:** React 19 + TypeScript + Vite, sin capas Clean Architecture
- **Umbrales de calidad backend:** pylint ≥ 8.0, CC ≤ 10, MI ≥ 20, cobertura ≥ 95%
- **Umbrales de calidad frontend (adaptados):** ESLint/oxlint 0 errores, `tsc --noEmit` 0
  errores, Vitest — cobertura de referencia ≥80%

## Rutas de Artefactos
- Contexto: `docs/plans/sp-adj-01/US-ADJ-05-context.md`
- BDD feature: `tests/features/sp-adj-01/US-ADJ-05-paginar-cuentas.feature`
- Plan: `docs/plans/sp-adj-01/US-ADJ-05-plan.md`
- Reporte: `docs/reports/sp-adj-01/US-ADJ-05-report.md`
- Quality report: `quality/reports/sp-adj-01/US-ADJ-05-quality.json`
