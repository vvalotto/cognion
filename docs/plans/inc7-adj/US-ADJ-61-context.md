# Contexto de Ejecución — US-ADJ-61

## Fuentes
- **Fuente HU:** `docs/specs/ajustes/US-ADJ-61.md`, Issue [#476](https://github.com/vvalotto/cognion/issues/476)
- **Fuente Arquitectura:** `CLAUDE.md` §"Arquitectura interna", `docs/design/domain/BC-actividad-evaluativa-modelo.md`
- **Fuente UX (Parte B):** `wireframes-actividad-evaluativa.md` §3.1/§3.2 + prototipo `actividad-evaluativa-periodo-abierto.html` — **gate UX: requiere actualización y aprobación de Víctor antes de tocar `frontend/`**

## Historia de Usuario
- **ID:** US-ADJ-61 · **Título:** La actividad cerrada se ve como cerrada para el Estudiante
- **Tipo:** fix backend (estado derivado de solo lectura) + frontend · **Puntos:** 3 · **Prioridad:** P2 (hallazgo #10 🟡 UAT v1)

## Decisiones de Ejecución
- Perfil `clean-architecture-bc`; BDD sí; fases 0 a 9.
- Parte A (backend) primero; Parte B (frontend) tras el gate UX, en un segundo PR (mismo criterio que US-ADJ-62).
- El escenario "Los informes del Docente no cambian" no se automatiza por BDD: no se toca ese código (`listar_actividades_abiertas` ya excluye cerradas); se deja constancia en el reporte.

## Umbrales de calidad
pylint ≥ 8.0, CC ≤ 10, MI ≥ 20; CodeGuard `--analysis-type full`; mypy/ruff 0 errores. Frontend: `tsc -b`, `oxlint`, vitest.

## Rutas de Artefactos
- BDD: `tests/features/inc7-adj/US-ADJ-61-actividad-cerrada-visible-estudiante.feature`; steps `tests/step_defs/inc7-adj/test_us_adj_61_steps.py`
- Plan: `docs/plans/inc7-adj/US-ADJ-61-plan.md` · Reporte: `docs/reports/inc7-adj/US-ADJ-61-report.md` · Quality: `quality/reports/inc7-adj/US-ADJ-61-quality.json`

## Regla de ejecución de tests
Integración y BDD solo contra base descartable con `DATABASE_URL` inline. Esta vez correr **todo `tests/unit/inc3`, `tests/integration/inc3` y los step_defs de `inc3`** (el cambio de `_estado_para` puede invertir tests de `US-3.4.5`; US-ADJ-62 mostró que acotar a inc5/inc7 deja tests viejos sin corregir).

## Hallazgos de Fase 0
- `_estado_para` no mira `cerrada_manualmente` ni `fecha_cierre`; `ActividadResumen` ya trae ambos.
- Test unitario `test_cerrada_sin_rendir_se_muestra_como_pendiente` afirma el comportamiento viejo: hay que invertirlo.
- `ActividadVisibleResponse.estado` ya es `str`: sin cambio de contrato.
