# Reporte de Implementación: US-3.3.1

## Resumen Ejecutivo

- **Historia de Usuario:** US-3.3.1 — Docente extiende (o intenta acortar) el plazo de una actividad vigente
- **Puntos estimados:** 5
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-28
- **Issue:** [#163](https://github.com/vvalotto/cognion/issues/163)
- **Spec:** `docs/specs/inc3/US-3.3.1.md`

Primera US de la Iteración 3 del Incremento 3 (RF-11b). Introduce el primer comando que agrega
un segundo evento al stream de `ActividadEvaluativaPeriodoAbierto`, que hasta acá siempre tenía
un único evento (`ActividadEvaluativaCreada`).

---

## Componentes Implementados

### Entities

- ✅ **`NoSePuedeAcortarConEvaluacionesActivas`, `ActividadYaCerrada`** (`entities/errors.py`) —
  errores de dominio para INV-AE-04/04b (`ActividadYaCerrada` compartida con `US-3.3.2`)
- ✅ **`PeriodoDisponibilidadModificado`** (`entities/eventos.py`) — segundo evento posible del
  stream de la actividad
- ✅ **`ActividadEvaluativaPeriodoAbierto.reconstruir()`** (nuevo) — primer replay real del
  stream de este aggregate, dispatch por `event_type` vía función de módulo `_aplicar_evento`
  (mismo patrón que `Evaluacion.reconstruir()`, `US-3.2.2`)
- ✅ **`ActividadEvaluativaPeriodoAbierto.validar_para_modificar_periodo()`** (nuevo) — valida
  INV-AE-02/04/04b sin mutar el aggregate (mismo criterio que
  `Evaluacion.validar_para_suspender()`)

### Use Cases

- ✅ **`ModificarPeriodoDisponibilidadUseCase`** (`use_cases/modificar_periodo_disponibilidad.py`)
  — orquesta la modificación, calcula `hay_evaluaciones_activas` filtrando
  `EvaluacionActivaQueryPort.listar_no_finalizadas()` por `actividad_id` (sin extender el port)
- ✅ **Ajuste obligatorio en 4 Use Case existentes** (`iniciar_evaluacion`, `registrar_respuesta`,
  `reanudar_evaluacion`, `verificar_vencimientos`) — dejan de leer `eventos_actividad[0].payload`
  directamente y usan `ActividadEvaluativaPeriodoAbierto.reconstruir(...)`, para que un cambio de
  período sea visible en el resto del BC

### Interface Adapters / Frameworks

- ✅ **`ActividadesController.modificar_periodo_disponibilidad()`** (extendido)
- ✅ **`ModificarPeriodoDisponibilidadRequest`** (`frameworks/api/schemas.py`)
- ✅ **`PATCH /actividades/{actividad_id}/periodo`** (`frameworks/api/actividades_router.py`,
  rol `docente`) — `ActividadNoExiste` → 404; `PeriodoInvalido`,
  `NoSePuedeAcortarConEvaluacionesActivas`, `ActividadYaCerrada` → 422
- ✅ **`dependencies.py`** — `get_actividades_controller` arma
  `ModificarPeriodoDisponibilidadUseCase` con `SQLAlchemyEvaluacionActivaQueryRepository`
  (`US-3.2.4`, reutilizada tal cual)

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint | 9.71/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 7 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (mínimo entre archivos del BC) | 60.40 | > 20 | ✅ |
| Cobertura de Tests (`entities/` + `use_cases/`, BC completo) | 100% | ≥ 95% | ✅ |
| mypy (`src/` completo) | 0 errores | 0 errores | ✅ |
| CodeGuard (archivos modificados/agregados) | 0 errores, 0 warnings | 0 CRITICAL | ✅ |

**Estado General:** ✅ APROBADO — `quality/reports/inc3/US-3.3.1-quality.json`

---

## Tests Implementados

### Tests Unitarios (23 tests nuevos)

- ✅ `test_actividad_evaluativa_periodo_abierto.py` (+11 tests) — `reconstruir()` (replay de 1 y
  2 eventos) y `validar_para_modificar_periodo()` (INV-AE-02/04/04b)
- ✅ `test_modificar_periodo_disponibilidad_use_case.py` (8 tests, nuevo) — extender/acortar,
  aislamiento entre actividades, rechazos, dos modificaciones sucesivas
- ✅ `test_actividades_controller.py` (+1 test) — delegación al Use Case nuevo

### Tests de Integración (7 tests nuevos)

- ✅ `test_modificar_periodo_disponibilidad_api_integration.py` — extender, acortar sin/con
  evaluación activa, período inválido, actividad inexistente, sin autenticación, rol insuficiente

### Escenarios BDD (6 escenarios)

- ✅ `US-3.3.1-modificar-periodo-disponibilidad.feature`
  - Extender el plazo siempre se permite
  - Acortar sin evaluaciones activas se permite
  - Acortar con evaluación EnCurso/Suspendida se rechaza (2 escenarios)
  - `nueva_fecha_cierre` anterior a `fecha_apertura` se rechaza
  - Actividad inexistente se rechaza

**Todos los tests pasando:** ✅ 138/138 unitarios del BC, 67/67 integración del BC, 6/6 BDD de
esta US. Suite completa del proyecto verificada antes de Fase 7: 312/312 unit, 195/195
integration, 119/120 step_defs (1 test preexistente de `US-3.2.1` falla por timing, confirmado
no-regresión — ver "Lecciones Aprendidas").

---

## Archivos Creados/Modificados

### Código de Producción — Nuevo

- `src/actividad_evaluativa/use_cases/modificar_periodo_disponibilidad.py`

### Código de Producción — Modificado

- `src/actividad_evaluativa/entities/errors.py`
- `src/actividad_evaluativa/entities/eventos.py`
- `src/actividad_evaluativa/entities/actividad_evaluativa_periodo_abierto.py`
- `src/actividad_evaluativa/use_cases/iniciar_evaluacion.py`
- `src/actividad_evaluativa/use_cases/registrar_respuesta.py`
- `src/actividad_evaluativa/use_cases/reanudar_evaluacion.py`
- `src/actividad_evaluativa/use_cases/verificar_vencimientos.py`
- `src/actividad_evaluativa/interface_adapters/controllers/actividades_controller.py`
- `src/actividad_evaluativa/frameworks/api/schemas.py`
- `src/actividad_evaluativa/frameworks/api/actividades_router.py`
- `src/actividad_evaluativa/frameworks/dependencies.py`

### Tests

- `tests/unit/inc3/test_actividad_evaluativa_periodo_abierto.py` (modificado)
- `tests/unit/inc3/test_modificar_periodo_disponibilidad_use_case.py` (nuevo)
- `tests/unit/inc3/test_actividades_controller.py` (modificado)
- `tests/integration/inc3/test_modificar_periodo_disponibilidad_api_integration.py` (nuevo)
- `tests/features/inc3/US-3.3.1-modificar-periodo-disponibilidad.feature` (nuevo)
- `tests/step_defs/inc3/test_us_3_3_1_steps.py` (nuevo)

### Documentación

- `docs/specs/inc3/US-3.3.1.md`
- `docs/plans/inc3/US-3.3.1-context.md`
- `docs/plans/inc3/US-3.3.1-plan.md`
- `docs/design/domain/BC-actividad-evaluativa-modelo.md` (nota de implementación)
- `docs/traceability/matrix.md` (RF-11b suma `US-3.3.1`)
- `docs/plans/inc3/inc3-candidatas.md` (Issue #163 registrado)
- `docs/reports/inc3/US-3.3.1-report.md` (este archivo)
- `quality/reports/inc3/US-3.3.1-quality.json`, `US-3.3.1-codeguard.json`

---

## Decisiones de diseño

1. **`reconstruir()` con replay real**, no una solución puntual — mismo patrón de dispatch por
   `event_type` que `Evaluacion.reconstruir()`/`_aplicar_evento` (`US-3.2.2`), para que el BC
   tenga un único criterio ante la aparición de un segundo tipo de evento en cualquier aggregate.
2. **Ajuste obligatorio de los 4 Use Case existentes** que leían el primer evento directamente
   — sin este cambio, un `ModificarPeriodoDisponibilidad` habría quedado invisible para el resto
   del BC (incluida la Regla 2 del `VerificadorDeVencimientos`, que podría finalizar evaluaciones
   contra una `fecha_cierre` ya extendida).
3. **`hay_evaluaciones_activas` calculado filtrando `listar_no_finalizadas()`**, sin extender
   `EvaluacionActivaQueryPort` — el resumen ya trae `actividad_id`, evita ensanchar el port por
   un filtro que se resuelve en una línea del Use Case.
4. **Escenario BDD de `ActividadYaCerrada` diferido a `US-3.3.2`** — su precondición
   (`cerrada_manualmente = true`) recién existe cuando `CerrarActividad` esté implementado; la
   validación en sí queda cubierta a nivel unitario (`test_actividad_cerrada_manualmente_se_rechaza`).

---

## Criterios de Aceptación (Issue #163)

- [x] `ModificarPeriodoDisponibilidad` extiende el plazo sin restricción adicional
- [x] Acortar se rechaza (`NoSePuedeAcortarConEvaluacionesActivas`) si existe `Evaluacion`
      `EnCurso` o `Suspendida`
- [x] Se rechaza (`ActividadYaCerrada`) si la actividad ya está cerrada manualmente
- [x] Se revalida `fecha_apertura` < `nueva_fecha_cierre` (`PeriodoInvalido`)
- [x] Evento `PeriodoDisponibilidadModificado` persistido en el stream de la actividad

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] `US-3.3.2` (Docente cierra una actividad manualmente) — reutilizará
      `FinalizarEvaluacionUseCase` con `actor="sistema"` para la cascada síncrona (Regla 3);
      agregará la verificación BDD end-to-end de `ActividadYaCerrada` diferida en esta US
- [ ] Cierra la Iteración 3 del Incremento 3 (backend) cuando `US-3.3.2` cierre
- [ ] Fix del test preexistente flaky `test_rechazo_fuera_del_período_vigente`
      (`US-3.2.1`) — ya reportado como tarea aparte, no bloquea esta US

---

## Lecciones Aprendidas

- ✅ Extender la firma de `reconstruir()` con el mismo patrón de dispatch ya usado en
  `Evaluacion` preservó el 100% de los tests y callers existentes de `US-3.1.3` a `US-3.2.4`.
- 💡 Un escenario BDD que depende de una US futura para construir su precondición no debe
  forzarse con un `skip` — se documenta como diferido y se cubre a nivel unitario mientras tanto.
- ⚠️ La suite completa de `step_defs` reveló un test preexistente (`US-3.2.1`) con una ventana de
  tiempo demasiado ajustada (~1s) para las llamadas HTTP de su propio setup — confirmado que
  falla igual en `develop` limpio, no es una regresión de esta US.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-28
