# Reporte de Implementación: US-3.2.2

## Resumen Ejecutivo

- **Historia de Usuario:** US-3.2.2 — Estudiante suspende y reanuda su evaluación
- **Puntos estimados:** 3
- **Tiempo real:** ~24 min (Fases 0-8 con tracking activo; PRIN-001 — tiempo real de ejecución del agente, no comparable contra estimación humana)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-27

---

## Componentes Implementados

### Entities (`src/actividad_evaluativa/entities/`)

- ✅ **`Evaluacion.validar_para_suspender()`/`validar_para_reanudar()`** (extendido) — aplican INV-AE-11/12, no mutan estado (mismo criterio de separación validación/mutación que `validar_para_registrar_respuesta`)
- ✅ **`Evaluacion.reconstruir()`** (reescrito) — dispatch por `event_type` en una función de módulo (`_aplicar_evento`) en vez de asumir que todo evento posterior al primero es `RespuestaRegistrada`
- ✅ **`EvaluacionSuspendida`, `EvaluacionReanudada`** (`entities/eventos.py`, nuevos) — el primero lleva `actor` (`"estudiante"` en esta US, `"sistema"` cuando `US-3.2.4` lo reutilice)
- ✅ **`EvaluacionYaSuspendida`, `EvaluacionNoSuspendida`** (`entities/errors.py`, nuevos)

### Use Cases (`src/actividad_evaluativa/use_cases/`)

- ✅ **`SuspenderEvaluacionUseCase`** (nuevo) — orquesta INV-AE-12, no valida período vigente (pausar siempre debe poder hacerse)
- ✅ **`ReanudarEvaluacionUseCase`** (nuevo) — orquesta INV-AE-11 + `FueraDePeriodo` (carga la actividad, mismo patrón que `RegistrarRespuestaUseCase`)

### Interface Adapters (`src/actividad_evaluativa/interface_adapters/`)

- ✅ **`EvaluacionesController`** (extendido) — pasa de 2 a 4 Use Case inyectados, métodos `suspender_evaluacion`/`reanudar_evaluacion`

### Frameworks (`src/actividad_evaluativa/frameworks/`)

- ✅ **`evaluaciones_router.py`** (extendido) — `POST /evaluaciones/{evaluacion_id}/suspender` y `.../reanudar` (rol `estudiante`), reutiliza `EvaluacionResponse` vía helper `_a_response` (también aplicado a `iniciar_evaluacion` para no duplicar la conversión)
- ✅ **`dependencies.py`** (extendido) — `get_evaluaciones_controller` arma también los dos Use Case nuevos

---

## API Endpoints

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| POST | `/evaluaciones/{evaluacion_id}/suspender` | Pausa explícita, `EnCurso → Suspendida` | ✅ rol `estudiante` |
| POST | `/evaluaciones/{evaluacion_id}/reanudar` | Reanudación explícita, `Suspendida → EnCurso` | ✅ rol `estudiante` |

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint | 9.89/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 6 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (mín) | 63.08 | > 20 | ✅ |
| Cobertura de Tests (`entities/`+`use_cases/`+`interface_adapters/`) | 100% | ≥ 95% | ✅ |

**Estado General:** ✅ APROBADO (`quality/reports/inc3/US-3.2.2-quality.json`)

> `codeguard` sobre los 8 `.py` nuevos/modificados de la US: 0 errores, 0 advertencias
> (`quality/reports/inc3/US-3.2.2-codeguard.json`). `mypy` sobre `src/` completo: 0 errores.
> `DesignReviewer` sobre `src/actividad_evaluativa/`: 0 CRITICAL, 28 WARNING (todas preexistentes
> de `US-3.2.1`, ninguna nueva). `frameworks/` excluido del gate de coverage por
> `pyproject.toml` (mismo criterio en todos los BCs) — cubierto por 11 tests de integración
> HTTP y 9 escenarios BDD contra la base local.

---

## Tests Implementados

### Tests Unitarios (23 tests nuevos — `tests/unit/inc3/`)

- ✅ `test_evaluacion.py` (+9) — replay aplicando `EvaluacionSuspendida`/`EvaluacionReanudada`, `validar_para_suspender`/`validar_para_reanudar` (las 3 transiciones válidas + inválidas)
- ✅ `test_suspender_evaluacion_use_case.py` (nuevo, 5) — suspende una `EnCurso`, evaluación inexistente, evaluación de otro estudiante, ya suspendida, no valida período
- ✅ `test_reanudar_evaluacion_use_case.py` (nuevo, 5) — reanuda una `Suspendida`, evaluación inexistente, evaluación de otro estudiante, no suspendida, fuera de período
- ✅ `test_errors.py` (+2) — los 2 errores de dominio nuevos
- ✅ `test_evaluaciones_controller.py` (+2) — delegación de `suspender_evaluacion`/`reanudar_evaluacion`, helper `_controller` para no repetir la construcción de 4 Use Case en cada test

### Tests de Integración (11 tests nuevos — `tests/integration/inc3/`)

- ✅ `test_suspender_reanudar_api_integration.py` (nuevo, 11) — suspende, reanuda, reanudar habilita volver a registrar respuestas, rechazo de `RegistrarRespuesta` sobre `Suspendida`, rechazo al suspender ya suspendida, rechazo al reanudar `EnCurso`, rechazo al reanudar fuera de período, suspender no valida período, evaluación inexistente, 401 sin auth, 403 con rol insuficiente

### Escenarios BDD (9 escenarios — `tests/features/inc3/US-3.2.2-suspender-reanudar-evaluacion.feature`)

- ✅ Estudiante suspende una evaluación en curso
- ✅ Estudiante reanuda una evaluación suspendida
- ✅ Reanudar habilita volver a registrar respuestas
- ✅ Rechazo al suspender una evaluación ya suspendida
- ✅ Rechazo al suspender una evaluación finalizada (a nivel de dominio — ver Lecciones Aprendidas)
- ✅ Rechazo al reanudar una evaluación en curso
- ✅ Rechazo al reanudar una evaluación finalizada (a nivel de dominio)
- ✅ Rechazo al reanudar fuera del período vigente (ventana real de ~3s + `sleep`)
- ✅ Suspender no valida período vigente

**Todos los tests pasando:** ✅ suite completa `unit/` + `integration/` + `step_defs/` sin regresiones (525 tests totales del proyecto, +43 de esta US)

---

## Archivos Creados

### Código de Producción

- `src/actividad_evaluativa/entities/evaluacion.py` (extendido)
- `src/actividad_evaluativa/entities/eventos.py` (extendido)
- `src/actividad_evaluativa/entities/errors.py` (extendido)
- `src/actividad_evaluativa/use_cases/suspender_evaluacion.py` (nuevo)
- `src/actividad_evaluativa/use_cases/reanudar_evaluacion.py` (nuevo)
- `src/actividad_evaluativa/interface_adapters/controllers/evaluaciones_controller.py` (extendido)
- `src/actividad_evaluativa/frameworks/api/evaluaciones_router.py` (extendido)
- `src/actividad_evaluativa/frameworks/dependencies.py` (extendido)

### Tests

- `tests/unit/inc3/test_evaluacion.py`, `test_errors.py`, `test_evaluaciones_controller.py` (extendidos)
- `tests/unit/inc3/test_suspender_evaluacion_use_case.py`, `test_reanudar_evaluacion_use_case.py` (nuevos)
- `tests/integration/inc3/test_suspender_reanudar_api_integration.py` (nuevo)
- `tests/features/inc3/US-3.2.2-suspender-reanudar-evaluacion.feature` (nuevo)
- `tests/step_defs/inc3/test_us_3_2_2_steps.py` (nuevo)

### Documentación

- `docs/specs/inc3/US-3.2.2.md`
- `docs/plans/inc3/US-3.2.2-context.md`, `US-3.2.2-plan.md`
- `docs/reports/inc3/US-3.2.2-report.md` (este archivo)
- `quality/reports/inc3/US-3.2.2-quality.json`, `US-3.2.2-codeguard.json`

> `docs/traceability/matrix.md` no se actualiza — igual que `US-3.1.1`/`US-2.1.2`/`US-2.1.6`,
> ningún RF/RNF de `RF_v1.md`/`RNF_v1.md` cubre explícitamente suspender/reanudar como
> escenario propio (RNF-CONF-1 ya quedó asociado a `US-3.2.1`, persistencia atómica). Es
> mecanismo de soporte del ciclo de vida de `Evaluacion`, no mueve fila.

---

## Criterios de Aceptación (`docs/specs/inc3/US-3.2.2.md`, Issue #156)

- [x] `SuspenderEvaluacion` pasa `EnCurso → Suspendida`, emite `EvaluacionSuspendida`
- [x] `ReanudarEvaluacion` pasa `Suspendida → EnCurso`, emite `EvaluacionReanudada`, mismo set y respuestas
- [x] `RegistrarRespuesta` sobre `Suspendida` sigue rechazando con `EvaluacionSuspendida` (verificado, sin tocar código de `US-3.2.1`)
- [x] Rechaza `SuspenderEvaluacion` sobre `Suspendida`/`Finalizada` con `EvaluacionYaSuspendida`/`EvaluacionYaFinalizada`
- [x] Rechaza `ReanudarEvaluacion` sobre `EnCurso`/`Finalizada` con `EvaluacionNoSuspendida`/`EvaluacionYaFinalizada`
- [x] Rechaza `ReanudarEvaluacion` fuera del período vigente con `FueraDePeriodo`

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] `US-3.2.3` (`FinalizarEvaluacion` + revisión, RF-13) — puede finalizar desde `EnCurso` o `Suspendida`
- [ ] `US-3.2.4` (`VerificadorDeVencimientos`, técnica) — reutiliza `SuspenderEvaluacionUseCase` tal cual con actor `"sistema"` (Regla 1, inactividad); el campo `actor` del evento ya está listo para eso
- [ ] `docs/traceability/matrix.md` — sin cambios pendientes de esta US

---

## Lecciones Aprendidas

- ✅ Reutilizar el patrón exacto de `RegistrarRespuestaUseCase`/`IniciarEvaluacionUseCase`
  (replay → validar invariante → armar evento → `append` con concurrencia optimista) hizo la
  implementación de los dos Use Case nuevos directa, sin decisiones de diseño pendientes.
- ✅ El patrón recurrente de CRITICAL de CBO de Incremento 2 no se repitió: `EvaluacionesController`
  pasando de 2 a 4 Use Case inyectados quedó lejos del umbral en `DesignReviewer`.
- 🐛 Dos de los 9 escenarios BDD (rechazo al suspender/reanudar una evaluación finalizada) no
  se pudieron implementar end-to-end vía HTTP porque `FinalizarEvaluacion` todavía no existe
  (llega con `US-3.2.3`) — se implementaron a nivel de dominio (`validar_para_suspender`/
  `validar_para_reanudar` directo), mismo criterio ya documentado en `US-3.2.1`.
- 🐛 El escenario "rechazo al reanudar fuera del período vigente" necesitó una ventana más
  generosa que la usada en `US-3.2.1` (500ms/1.5s): con más pasos previos (suspender antes de
  reanudar) el overhead de las llamadas HTTP hacía que la actividad ya estuviera vencida al
  momento de `IniciarEvaluacion`, antes de siquiera llegar al escenario bajo prueba. Se resolvió
  con 1s/3s de ventana + `sleep(4)` — a tener en cuenta en `US-3.2.3`/`US-3.2.4`, que van a
  necesitar escenarios similares con aún más pasos previos.
- 💡 Extraer `_a_response` en el router (reutilizado por los 3 endpoints que devuelven
  `Evaluacion`) evitó triplicar la construcción de `EvaluacionResponse` sin necesidad de tocar
  el schema.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-27
