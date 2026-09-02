# Reporte de Implementación: US-3.2.4

## Resumen Ejecutivo

- **Historia de Usuario:** US-3.2.4 — VerificadorDeVencimientos: suspensión y finalización automáticas
- **Puntos estimados:** 5
- **Tiempo real (tracker):** ~35 min efectivos (Fases 0 a 9)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-27
- **Issue:** [#159](https://github.com/vvalotto/cognion/issues/159)
- **Spec:** `docs/specs/inc3/US-3.2.4.md`

Cierra completa la Iteración 2 del Incremento 3 (backend): a partir de esta US, ninguna
`Evaluacion` puede quedar indefinidamente `EnCurso` sin actividad, ni sobrevivir pasivamente al
cierre del período de una actividad.

---

## Componentes Implementados

### Entities/Ports

- ✅ **`EvaluacionActivaQueryPort`** (`src/actividad_evaluativa/entities/ports/evaluacion_activa_query_port.py`)
  - VO `EvaluacionActivaResumen` (`evaluacion_id`, `actividad_id`, `estado`, `ultima_actividad_en`)
  - Separación command/query respecto de `EventStorePort` — mismo criterio ya aplicado en
    Incremento 2 (`CuentaQueryPort`, `BancosController`)

### Use Cases

- ✅ **`SuspenderEvaluacionUseCase`/`FinalizarEvaluacionUseCase`** (extendidos, no reescritos)
  - `execute()` gana `estudiante_id: UUID | None = None, *, actor: str = "estudiante"`
  - `actor="estudiante"` (default): comportamiento idéntico al de `US-3.2.2`/`US-3.2.3`, sin
    tocar ningún caller HTTP existente
  - `actor="sistema"`: sin chequeo de pertenencia, captura `EvaluacionYaSuspendida`/
    `EvaluacionYaFinalizada` como no-op silencioso (idempotencia de la Policy)
- ✅ **`VerificarVencimientosUseCase`** (`src/actividad_evaluativa/use_cases/verificar_vencimientos.py`)
  - Orquesta la Regla 1 (inactividad) y la Regla 2 (vencimiento de período)
  - Sin comando ni evento propio — reutiliza los dos Use Case anteriores con `actor="sistema"`
  - `ResumenVerificacion(suspendidas, finalizadas)` como resultado de cada corrida

### Frameworks

- ✅ **`SQLAlchemyEvaluacionActivaQueryRepository`** (`src/actividad_evaluativa/frameworks/adapters/evaluacion_activa_query_repository.py`)
  - Implementa el read model como **query de lectura** sobre la tabla `events` existente
    (agrupada en memoria por `aggregate_id`), no como tabla sincronizada aparte — decisión de
    diseño 2 de la spec, confirmada con Víctor
- ✅ **Background task en `src/app.py`** — `asyncio.create_task` en el `lifespan` de FastAPI,
  cadencia configurable (`verificador_vencimientos_cadencia_segundos`, default 120s)
- ✅ **Settings nuevos** (`src/settings.py`): `verificador_vencimientos_cadencia_segundos`,
  `verificador_vencimientos_umbral_inactividad_minutos` (default 15 min)
- ✅ **Factory `build_verificar_vencimientos_use_case`** (`dependencies.py`) — recibe la sesión
  directamente, sin `Depends` de FastAPI (corre fuera del ciclo request/response)

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint | 9.74/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 6 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (mínimo entre archivos tocados) | 67.11 | > 20 | ✅ |
| Cobertura de Tests (`entities/` + `use_cases/`) | 100% | ≥ 95% | ✅ |
| mypy (`src/` completo) | 0 errores | 0 errores | ✅ |
| CodeGuard (archivos modificados/agregados) | 0 errores, 0 warnings | 0 CRITICAL | ✅ |

**Estado General:** ✅ APROBADO — `quality/reports/inc3/US-3.2.4-quality.json`

---

## Tests Implementados

### Tests Unitarios (17 tests nuevos)

- ✅ `test_verificar_vencimientos_use_case.py` (7 tests) — Reglas 1/2, idempotencia, caché de
  `fecha_cierre` entre evaluaciones de la misma actividad
- ✅ `test_evaluacion_activa_query_repository.py` (5 tests) — derivación pura de estado/
  `ultima_actividad_en` a partir del stream de eventos (`_resumen_de_stream`)
- ✅ `test_suspender_evaluacion_use_case.py` (+3 tests) — modo `actor="sistema"`
- ✅ `test_finalizar_evaluacion_use_case.py` (+2 tests) — modo `actor="sistema"`

### Tests de Integración (4 tests nuevos)

- ✅ `test_verificar_vencimientos_integration.py` — Reglas 1/2 y idempotencia contra PostgreSQL
  real, backdateando `occurred_at`/`fecha_cierre` vía SQL directo para simular inactividad y
  vencimiento sin esperar tiempo real

### Escenarios BDD (7 escenarios)

- ✅ `US-3.2.4-verificador-vencimientos.feature`
  - Regla 1 suspende una Evaluacion inactiva
  - Regla 1 no afecta una Evaluacion con actividad reciente
  - Regla 2 finaliza una Evaluacion EnCurso/Suspendida de actividad vencida (2 escenarios)
  - Regla 2 no afecta evaluaciones de actividad vigente
  - Idempotencia — segunda corrida es no-op
  - Evaluacion ya Finalizada nunca se reconsidera

**Todos los tests pasando:** ✅ 134/134 (suite completa de `US-3.2.4`), 599/599 (unit +
integration + step_defs del proyecto completo, verificado antes de Fase 7)

---

## Archivos Creados/Modificados

### Código de Producción — Nuevo

- `src/actividad_evaluativa/entities/ports/evaluacion_activa_query_port.py`
- `src/actividad_evaluativa/use_cases/verificar_vencimientos.py`
- `src/actividad_evaluativa/frameworks/adapters/evaluacion_activa_query_repository.py`

### Código de Producción — Modificado

- `src/actividad_evaluativa/use_cases/suspender_evaluacion.py`
- `src/actividad_evaluativa/use_cases/finalizar_evaluacion.py`
- `src/actividad_evaluativa/interface_adapters/controllers/evaluaciones_controller.py`
- `src/actividad_evaluativa/frameworks/dependencies.py`
- `src/app.py`
- `src/settings.py`

### Tests

- `tests/unit/inc3/test_verificar_vencimientos_use_case.py` (nuevo)
- `tests/unit/inc3/test_evaluacion_activa_query_repository.py` (nuevo)
- `tests/unit/inc3/test_suspender_evaluacion_use_case.py` (modificado)
- `tests/unit/inc3/test_finalizar_evaluacion_use_case.py` (modificado)
- `tests/integration/inc3/test_verificar_vencimientos_integration.py` (nuevo)
- `tests/features/inc3/US-3.2.4-verificador-vencimientos.feature` (nuevo)
- `tests/step_defs/inc3/test_us_3_2_4_steps.py` (nuevo)

### Documentación

- `docs/specs/inc3/US-3.2.4.md`
- `docs/plans/inc3/US-3.2.4-context.md`
- `docs/plans/inc3/US-3.2.4-plan.md`
- `docs/design/domain/BC-actividad-evaluativa-modelo.md` (nota de implementación en §6b)
- `docs/reports/inc3/US-3.2.4-report.md` (este archivo)
- `quality/reports/inc3/US-3.2.4-quality.json`

---

## Decisiones de diseño confirmadas con Víctor (2026-08-27)

1. **Read model como query de lectura**, no tabla sincronizada — evita tocar 4 Use Case ya
   cerrados y una migración nueva, sin riesgo de desincronización.
2. **Cadencia del background task: 120 segundos.**
3. **`UMBRAL_INACTIVIDAD`: 15 minutos.**
4. **Extensión de firma** (`estudiante_id` opcional + `actor`) en vez de reuso literal "tal
   cual" de los Use Case existentes — el Issue/modelo no contemplaban que la Policy no tiene un
   `estudiante_id` de contexto.

---

## Criterios de Aceptación (Issue #159)

- [x] Regla 1 (inactividad) dispara `SuspenderEvaluacion` con actor `sistema`
- [x] Regla 2 (vencimiento del período) dispara `FinalizarEvaluacion` con actor `sistema`
- [x] Ambas reglas son idempotentes (no-op silencioso protegido por INV-AE-11/12)
- [x] Read model de evaluaciones activas construido (como query de lectura, decisión confirmada)
- [x] Queries de evaluaciones inactivas/de actividades vencidas implementadas (como filtros
      internos de `VerificarVencimientosUseCase` sobre el resultado del read model)
- [x] Cadencia de ejecución definida (background task `asyncio`, 120s)

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] `US-3.3.1` (Docente extiende/acorta el plazo de una actividad vigente, Iteración 3) — al
      implementar `ModificarPeriodoDisponibilidad`, la Regla 2 deberá reconstruir el stream
      completo de `ActividadEvaluativaPeriodoAbierto` en vez de leer solo el primer evento
      (nota dejada en `docs/specs/inc3/US-3.2.4.md`, Decisión de diseño 4)
- [ ] `US-3.3.2` (Docente cierra una actividad manualmente) — reutilizará
      `FinalizarEvaluacionUseCase` con `actor="sistema"` para la cascada síncrona (Regla 3)
- [ ] Cierra la Iteración 2 del Incremento 3 (backend) — siguiente paso es la Iteración 3
      (RF-11b: modificación del período de disponibilidad)

---

## Lecciones Aprendidas

- ✅ Extender la firma de un Use Case existente con un parámetro `actor` (en vez de duplicar
  lógica para el disparo automático) preservó el 100% de los tests y callers existentes de
  `US-3.2.2`/`US-3.2.3`.
- 💡 Implementar el read model como query de lectura sobre el event store existente, en vez de
  una proyección sincronizada por evento, evitó tocar código ya cerrado — válido a esta escala
  (30-60 alumnos), documentado como decisión reversible si el volumen cambia.
- 💡 Backdatear `occurred_at`/`fecha_cierre` vía SQL directo en los tests de integración/BDD
  evitó usar `time.sleep()` largos para simular vencimiento de período (a diferencia de
  `US-3.2.2`, que sí usa `time.sleep(4)` para el caso de `FueraDePeriodo`).

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-27
