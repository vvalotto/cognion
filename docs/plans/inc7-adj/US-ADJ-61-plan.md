# Plan de Implementación — US-ADJ-61

Spec: `docs/specs/ajustes/US-ADJ-61.md` · Contexto: `US-ADJ-61-context.md` · BDD: 5 escenarios (Parte A).
Solo lectura: sin migración, sin puertos ni eventos nuevos.

## Parte A — Backend (esta corrida)
- [ ] **T1** `listar_actividades_visibles.py`: `EstadoVisible` documenta `"cerrada"`; `_estado_para` en el orden finalizada → cerrada (`cerrada_manualmente or fecha_cierre <= ahora`) → todavia_no_abrio → pendiente; docstring corregido (hoy afirma "solo 3 estados"). `ActividadVisibleResponse.estado` ya es `str`.

## Parte B — Frontend (bloqueada por gate UX, segundo PR)
- [ ] **T2** Actualizar `wireframes-actividad-evaluativa.md` §3.1/§3.2 y prototipo (`#est-actividades`, `#est-fuera-periodo`): 4.º badge "Cerrada", mensaje "Esta actividad ya cerró", retiro de la nota al pie; aprobación de Víctor.
- [ ] **T3** `actividad-evaluativa-api.ts` (`EstadoVisible`), `badge.tsx` (variante `visible-cerrada`), `MisActividades.tsx` (etiqueta y navegación), `FueraDePeriodo.tsx` (3 variantes según `state.estado`, texto neutro sin `state`).

## Tests (Fases 4-6)
- Invertir `test_cerrada_sin_rendir_se_muestra_como_pendiente` en `tests/unit/inc3/test_listar_actividades_visibles_use_case.py`; agregar: cerrada manual, vencida por fecha, `finalizada` gana a `cerrada`.
- BDD: `tests/step_defs/inc7-adj/test_us_adj_61_steps.py` (HTTP sobre `GET` de actividades visibles, base descartable).
- Regresión: correr **todo** `tests/unit/inc3`, `tests/integration/inc3` y los step_defs de `inc3` en base descartable.

## Docs (Fase 8)
`docs/specs/inc3/US-3.4.5.md` (nota "Enmendada por US-ADJ-61"), spec de esta US, reporte.

## Riesgos
- Tests de `US-3.4.5`/`3.4.6` que asuman "pendiente" para una actividad vencida: se detectan con la regresión de `inc3`.
- `MisMaterias.tsx` no cambia: ya cuenta solo `estado === "pendiente"`.
