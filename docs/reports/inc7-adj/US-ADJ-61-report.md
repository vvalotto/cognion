# Reporte de Implementación: US-ADJ-61

## Resumen Ejecutivo

- **Historia de Usuario:** US-ADJ-61 — La actividad cerrada se ve como cerrada para el Estudiante
- **Iteración:** `Incremento 7-ADJ` (cuarta US)
- **Puntos estimados:** 3 · **Tiempo real:** ver `.claude/tracking/US-ADJ-61-tracking.json` (PRIN-001)
- **Estado:** ✅ Parte A (backend) COMPLETADA · ⏳ Parte B (frontend) pendiente del gate UX
- **Fecha completado (Parte A):** 2026-10-04
- **Origen:** UAT v1, hallazgo **#10** 🟡
- **Aporta:** el listado del Estudiante devuelve `estado = "cerrada"` para una actividad cerrada a mano o vencida por fecha que no rindió, en vez de "pendiente".

## Componentes Implementados

- ✅ `use_cases/listar_actividades_visibles.py` — `_estado_para` con el orden finalizada → cerrada (`cerrada_manualmente or fecha_cierre <= ahora`) → todavia_no_abrio → pendiente; `EstadoVisible` y docstrings actualizados. Mismo criterio que `actividades_router._estado_actividad` del Docente. Sin cambio de contrato HTTP (`estado` ya era `str`).
- ⏳ Frontend (`actividad-evaluativa-api.ts`, `badge.tsx`, `MisActividades.tsx`, `FueraDePeriodo.tsx`) — pendiente del gate UX: actualizar wireframes §3.1/§3.2 y prototipo y obtener la aprobación de Víctor.
- ✅ Docs: spec de esta US y `US-3.4.5.md` (enmendada).

## Tests

| Nivel | Resultado |
|-------|-----------|
| Unit | 881/881 ✅ (invertido `test_cerrada_sin_rendir…` y 3 casos nuevos en `test_listar_actividades_visibles_use_case.py`) |
| BDD | 5/5 ✅ (`tests/step_defs/inc7-adj/test_us_adj_61_steps.py`) |
| Regresión `inc3` (integración + BDD, base descartable) | 177 ✅ · 3 ❌ **preexistentes** |

Los 3 fallos (`test_us_3_2_1` "rechazo fuera del período vigente"; `test_us_3_2_2` "rechazo al reanudar fuera del período" y "suspender no valida período") fallan con `KeyError: 'id'` en el setup y **fallan igual sin este cambio** (verificado con el archivo stasheado). El primero es el flake conocido de la Iteración 3 del Incremento 3; los otros dos no estaban registrados: conviene abrir un ítem aparte.

Verificación: `mypy` 0 errores, `ruff` limpio, `pylint` 9,76 (aviso preexistente R0903), CC A, MI 69,34. CodeGuard `--analysis-type full`: 5 errores de tooling (vulture/codespell no instalados, timeouts). Detalle en `quality/reports/inc7-adj/US-ADJ-61-quality.json`.

## Decisiones y notas

- El escenario "Los informes del Docente no cambian" no se automatizó: no se toca ese código (`listar_actividades_abiertas` ya excluye cerradas).
- Sin cambios en `MisMaterias.tsx`: cuenta solo `estado === "pendiente"`, que ahora excluye las cerradas.

## Incidente propio (transparencia)

Un `sed -i` con sintaxis GNU falló en macOS dentro de una cadena con `&&`; eso dejó sin definir la variable con la URL de la base descartable y lanzó una corrida de pytest en segundo plano **sin** `DATABASE_URL` inline, que podría haber apuntado a la base de desarrollo `cognion` (la cortó a los segundos). Esa base tiene 0 usuarios; ya estaba vacía desde el incidente de US-ADJ-60, así que no se puede asegurar si esta corrida la afectó. A partir de ahí, `DATABASE_URL` va inline en el mismo comando y con un chequeo previo.

## Próximos pasos

1. Gate UX: wireframes §3.1/§3.2 y prototipo (badge "Cerrada", "Esta actividad ya cerró", retiro de la nota al pie) → aprobación de Víctor.
2. Parte B (frontend) y cierre del Issue #476.
3. Abrir ítem para los 2 tests preexistentes de `US-3.2.2` que fallan.
