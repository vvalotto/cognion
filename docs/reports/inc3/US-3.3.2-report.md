# Reporte de Implementación: US-3.3.2

## Resumen Ejecutivo

- **Historia de Usuario:** US-3.3.2 — Docente cierra una actividad manualmente antes de tiempo
- **Puntos estimados:** 5
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-28
- **Issue:** [#164](https://github.com/vvalotto/cognion/issues/164)
- **Spec:** `docs/specs/inc3/US-3.3.2.md`

Segunda y última US de la Iteración 3 del Incremento 3 (RF-11b). Implementa la Regla 3 del
`VerificadorDeVencimientos` (cascada síncrona de finalización, no vía el job periódico) y cierra
completa la Iteración 3 (backend).

---

## Componentes Implementados

### Entities

- ✅ **`ActividadEvaluativaCerrada`** (`entities/eventos.py`) — tercer evento posible del stream
  de la actividad, terminal
- ✅ **`_aplicar_evento`** (extendido) — nueva rama `"ActividadEvaluativaCerrada"` →
  `cerrada_manualmente = True`
- ✅ **`ActividadEvaluativaPeriodoAbierto.validar_para_cerrar()`** (nuevo) — valida INV-AE-04b,
  sin restricción adicional (cerrar con evaluaciones activas es el caso de uso)
- ✅ **`ActividadYaCerrada`** — reutilizada tal cual, ya existía desde `US-3.3.1`

### Use Cases

- ✅ **`CerrarActividadUseCase`** (`use_cases/cerrar_actividad.py`) — emite
  `ActividadEvaluativaCerrada` y, en la misma invocación, reutiliza `FinalizarEvaluacionUseCase`
  con `actor="sistema"` (mecanismo de `US-3.2.4`) por cada `Evaluacion` `EnCurso`/`Suspendida` de
  la actividad, filtrando `EvaluacionActivaQueryPort.listar_no_finalizadas()` por `actividad_id`
  (mismo criterio que `ModificarPeriodoDisponibilidadUseCase`, sin extender el port)

### Interface Adapters / Frameworks

- ✅ **`ActividadesController.cerrar_actividad()`** (extendido, tercer Use Case inyectado)
- ✅ **`POST /actividades/{actividad_id}/cerrar`** (`frameworks/api/actividades_router.py`, rol
  `docente`, sin body) — `ActividadNoExiste` → 404; `ActividadYaCerrada` → 422
- ✅ **`_a_response()`** (extraído en el router) — evita una tercera copia del bloque de
  construcción de `ActividadResponse`, baja la advertencia de duplicate-code de `US-3.3.1`
- ✅ **`dependencies.py`** — `get_actividades_controller` arma `CerrarActividadUseCase` con
  `FinalizarEvaluacionUseCase(event_store)` reutilizado tal cual

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint | 9.70/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 7 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (mínimo entre archivos del BC) | 60.40 | > 20 | ✅ |
| Cobertura de Tests (`entities/` + `use_cases/`, BC completo) | 100% | ≥ 95% | ✅ |
| mypy (`src/` completo) | 0 errores | 0 errores | ✅ |
| CodeGuard (archivos modificados/agregados) | 0 errores, 0 warnings | 0 CRITICAL | ✅ |

**Estado General:** ✅ APROBADO — `quality/reports/inc3/US-3.3.2-quality.json`

---

## Tests Implementados

### Tests Unitarios (12 tests nuevos)

- ✅ `test_actividad_evaluativa_periodo_abierto.py` (+3 tests) — `reconstruir()` aplicando
  `ActividadEvaluativaCerrada`, `validar_para_cerrar()` (permite/rechaza)
- ✅ `test_cerrar_actividad_use_case.py` (5 tests, nuevo) — sin evaluaciones activas, cascada
  sobre `Evaluacion` `EnCurso`, aislamiento entre actividades, rechazo por ya cerrada, actividad
  inexistente
- ✅ `test_actividades_controller.py` (+1 test) — delegación al Use Case nuevo

### Tests de Integración (7 tests nuevos)

- ✅ `test_cerrar_actividad_api_integration.py` — sin evaluaciones activas, cascada con
  `Evaluacion` `EnCurso` (verificada vía `GET /evaluaciones/{id}/revision`), ya cerrada,
  `ModificarPeriodoDisponibilidad` sobre actividad cerrada, actividad inexistente, sin
  autenticación, rol insuficiente

### Escenarios BDD (6 escenarios)

- ✅ `US-3.3.2-cerrar-actividad.feature`
  - Cerrar sin evaluaciones activas
  - Cerrar finaliza en cascada evaluaciones `EnCurso` (2 evaluaciones)
  - Cerrar finaliza en cascada evaluaciones `Suspendida`
  - Cerrar una actividad ya cerrada se rechaza
  - **Modificar el período después de un cierre manual se rechaza** — escenario diferido de
    `US-3.3.1`, verificado end-to-end acá por primera vez
  - Cerrar una actividad inexistente se rechaza

**Todos los tests pasando:** ✅ 147/147 unitarios del BC, 74/74 integración del BC, 6/6 BDD de
esta US. Suite completa del proyecto verificada antes de Fase 7: 321/321 unit, 202/202
integration, 125/126 step_defs (1 test preexistente de `US-3.2.1`, ya reportado, sigue sin
tocar).

---

## Archivos Creados/Modificados

### Código de Producción — Nuevo

- `src/actividad_evaluativa/use_cases/cerrar_actividad.py`

### Código de Producción — Modificado

- `src/actividad_evaluativa/entities/eventos.py`
- `src/actividad_evaluativa/entities/actividad_evaluativa_periodo_abierto.py`
- `src/actividad_evaluativa/interface_adapters/controllers/actividades_controller.py`
- `src/actividad_evaluativa/frameworks/api/actividades_router.py`
- `src/actividad_evaluativa/frameworks/dependencies.py`

### Tests

- `tests/unit/inc3/test_actividad_evaluativa_periodo_abierto.py` (modificado)
- `tests/unit/inc3/test_cerrar_actividad_use_case.py` (nuevo)
- `tests/unit/inc3/test_actividades_controller.py` (modificado)
- `tests/integration/inc3/test_cerrar_actividad_api_integration.py` (nuevo)
- `tests/features/inc3/US-3.3.2-cerrar-actividad.feature` (nuevo)
- `tests/step_defs/inc3/test_us_3_3_2_steps.py` (nuevo)

### Documentación

- `docs/specs/inc3/US-3.3.2.md` (redactada junto con `US-3.3.1`, previa a esta ejecución)
- `docs/plans/inc3/US-3.3.2-context.md`
- `docs/plans/inc3/US-3.3.2-plan.md`
- `docs/design/domain/BC-actividad-evaluativa-modelo.md` (dos notas de implementación)
- `docs/traceability/matrix.md` (RF-11b suma `US-3.3.2`)
- `docs/reports/inc3/US-3.3.2-report.md` (este archivo)
- `quality/reports/inc3/US-3.3.2-quality.json`, `US-3.3.2-codeguard.json`

---

## Decisiones de diseño

1. **Cascada síncrona dentro del propio Use Case**, no un mecanismo de eventos/handlers —
   `CerrarActividadUseCase.execute()` emite el evento y llama `FinalizarEvaluacionUseCase` en un
   bucle simple, mismo nivel de infraestructura que el resto del proyecto (`ADR-009`, sin bus de
   eventos).
2. **Sin transacción única para las N finalizaciones + el cierre** — cada `Evaluacion` conserva
   su propia Unit of Work, documentado en la spec como aceptable a esta escala (30-60 alumnos).
3. **`_a_response()` extraído en el router** — al agregar el tercer endpoint que devuelve
   `ActividadResponse`, factorizar el bloque evitó agravar la advertencia de duplicate-code que
   ya había quedado en `US-3.3.1`.

---

## Criterios de Aceptación (Issue #164)

- [x] `CerrarActividad(actividad_id)` marca `cerrada_manualmente = true` y persiste
      `ActividadEvaluativaCerrada`
- [x] Toda `Evaluacion` `EnCurso`/`Suspendida` de esa actividad se finaliza de inmediato,
      síncronamente, reutilizando `FinalizarEvaluacionUseCase` con `actor="sistema"`
- [x] Repetir `CerrarActividad` sobre una actividad ya cerrada es rechazado
      (`ActividadYaCerrada`), no reemite el evento
- [x] Una vez cerrada, `ModificarPeriodoDisponibilidad` sobre la misma actividad también se
      rechaza con `ActividadYaCerrada`

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] **Cierra completa la Iteración 3 del Incremento 3 (backend)** — siguiente paso es la
      Iteración 4 (frontend), que consume las Iteraciones 1 a 3 de una sola vez
      (`US-3.4.1` a `US-3.4.7`, `docs/plans/inc3/inc3-candidatas.md`)
- [ ] Fix del test preexistente flaky `test_rechazo_fuera_del_período_vigente`
      (`US-3.2.1`) — ya reportado como tarea aparte

---

## Lecciones Aprendidas

- ✅ Reutilizar `FinalizarEvaluacionUseCase` con `actor="sistema"` para la cascada síncrona no
  requirió ningún cambio en ese Use Case — la extensión de firma de `US-3.2.4` sirvió tal cual.
- ✅ El escenario BDD diferido de `US-3.3.1` se verificó end-to-end sin cambios de código
  adicionales — la validación ya estaba correcta desde esa US.
- 💡 Extraer `_a_response()` en el router evitó una tercera copia del mismo bloque y bajó una
  advertencia de duplicate-code preexistente.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-28
