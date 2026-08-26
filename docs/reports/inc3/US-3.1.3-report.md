# Reporte de Implementación: US-3.1.3

## Resumen Ejecutivo

- **Historia de Usuario:** US-3.1.3 — Estudiante inicia su evaluación (set aleatorio fijo)
- **Puntos estimados:** 5
- **Tiempo real:** ~20 min (suma de fases con tracking activo; PRIN-001 — tiempo real de ejecución del agente, no comparable contra estimación humana)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-26

---

## Componentes Implementados

### Entities (`src/actividad_evaluativa/entities/`)

- ✅ **`Evaluacion` / `PreguntaAsignada` / `EstadoEvaluacion`** (`entities/evaluacion.py`) — aggregate root con `id` determinístico (`id_para`, `uuid5` sobre `(actividad_id, estudiante_id)`), factory `crear()`, `armar_preguntas_asignadas()`, `reconstruir()` (replay puro del propio stream)
- ✅ **`EvaluacionIniciada`** (`entities/eventos.py`, extendido) — único evento de esta US
- ✅ **`ActividadNoExiste`, `EstudianteNoExiste`, `FueraDePeriodo`** (`entities/errors.py`, extendido) — errores de dominio nuevos
- ✅ **`EstudianteConsultaPort`** (`entities/ports/estudiante_consulta_port.py`, nuevo) — puerto hacia BC Identidad, valida existencia + rol Estudiante
- ✅ **`PreguntaConsultaPort.listar_ids_activas_por_materia`** (extendido) — base del sampleo aleatorio (RF-12)

### Use Cases (`src/actividad_evaluativa/use_cases/`)

- ✅ **`IniciarEvaluacionUseCase`** — orquesta INV-AE-05/06, `FueraDePeriodo`, sampleo aleatorio (`random.sample`), idempotencia por stream determinístico

### Interface Adapters (`src/actividad_evaluativa/interface_adapters/`)

- ✅ **`EvaluacionesController`** — adapta requests HTTP al use case

### Frameworks (`src/actividad_evaluativa/frameworks/`)

- ✅ **`EstudianteConsultaPortInProcess`** (nuevo) — invoca `SQLAlchemyUsuarioRepository` de Identidad in-process
- ✅ **`PreguntaConsultaPortInProcess.listar_ids_activas_por_materia`** (extendido) — resuelve el `Banco` de la materia, mismo camino que `contar_activas_por_materia`
- ✅ **`schemas.py`** (extendido) — `IniciarEvaluacionRequest`/`PreguntaAsignadaResponse`/`EvaluacionResponse`
- ✅ **`evaluaciones_router.py`** (nuevo) — `POST /evaluaciones` (rol `estudiante`, `estudiante_id` desde JWT), mapea `ActividadNoExiste`/`EstudianteNoExiste`→404, `FueraDePeriodo`→422
- ✅ **`dependencies.py`** (extendido) — `get_evaluaciones_controller`, `require_estudiante`
- ✅ `src/app.py` — `evaluaciones_router` registrado

---

## API Endpoints

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| POST | `/evaluaciones` | Inicia (o retoma) la evaluación del Estudiante autenticado | ✅ rol `estudiante` |

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint | 9.68/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 2 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (mín) | 67.32 | > 20 | ✅ |
| Cobertura de Tests (`entities/`+`use_cases/`+`interface_adapters/`) | 100% | ≥ 95% | ✅ |

**Estado General:** ✅ APROBADO (`quality/reports/inc3/US-3.1.3-quality.json`)

> `codeguard` sobre los 13 `.py` nuevos/modificados de la US: 0 errores, 0 warnings, 39 infos
> (`quality/reports/inc3/US-3.1.3-codeguard.json`). `frameworks/` excluido del gate de coverage
> por `pyproject.toml` (mismo criterio en todos los BCs) — cubierto en cambio por 9 tests de
> integración HTTP y 5 escenarios BDD contra la base local.

---

## Tests Implementados

### Tests Unitarios (19 tests nuevos — `tests/unit/inc3/`)

- ✅ `test_evaluacion.py` (5 tests) — `id_para` determinístico, `crear()`, `reconstruir()`
- ✅ `test_iniciar_evaluacion_use_case.py` (7 tests) — creación, idempotencia, sets distintos por estudiante, 4 rechazos de dominio
- ✅ `test_evaluaciones_controller.py` (1 test) — delegación al use case
- ✅ `test_errors.py` (extendido, +3 tests) — los 3 errores de dominio nuevos

### Tests de Integración (9 tests nuevos — `tests/integration/inc3/`)

- ✅ `test_evaluaciones_api_integration.py` (9 tests) — `POST /evaluaciones` contra PostgreSQL local vía HTTP real: creación, idempotencia, sets propios por estudiante, 2 rechazos por período, actividad inexistente, 401 sin auth, 403 con rol insuficiente

### Escenarios BDD (5 escenarios — `tests/features/inc3/US-3.1.3-iniciar-evaluacion.feature`)

- ✅ Estudiante inicia su evaluación por primera vez
- ✅ Reconexión — idempotencia sin nuevo set
- ✅ Dos estudiantes reciben sets distintos
- ✅ Rechazo antes de la apertura
- ✅ Rechazo después del cierre

**Todos los tests pasando:** ✅ suite completa `unit/` + `integration/` + `step_defs/` sin regresiones (365 tests unit+integration, 82 escenarios BDD)

---

## Archivos Creados

### Código de Producción

- `src/actividad_evaluativa/entities/evaluacion.py` (nuevo)
- `src/actividad_evaluativa/entities/eventos.py` (extendido)
- `src/actividad_evaluativa/entities/errors.py` (extendido)
- `src/actividad_evaluativa/entities/ports/estudiante_consulta_port.py` (nuevo)
- `src/actividad_evaluativa/entities/ports/pregunta_consulta_port.py` (extendido)
- `src/actividad_evaluativa/use_cases/iniciar_evaluacion.py` (nuevo)
- `src/actividad_evaluativa/interface_adapters/controllers/evaluaciones_controller.py` (nuevo)
- `src/actividad_evaluativa/frameworks/adapters/estudiante_consulta_port_in_process.py` (nuevo)
- `src/actividad_evaluativa/frameworks/adapters/pregunta_consulta_port_in_process.py` (extendido)
- `src/actividad_evaluativa/frameworks/api/schemas.py` (extendido)
- `src/actividad_evaluativa/frameworks/api/evaluaciones_router.py` (nuevo)
- `src/actividad_evaluativa/frameworks/dependencies.py` (extendido)
- `src/app.py` (modificado — registro del router)

### Tests

- `tests/unit/inc3/_fakes.py` (extendido — `FakeEstudianteConsultaPort`, `listar_ids_activas_por_materia`)
- `tests/unit/inc3/test_evaluacion.py`, `test_iniciar_evaluacion_use_case.py`, `test_evaluaciones_controller.py` (nuevos)
- `tests/unit/inc3/test_errors.py` (extendido)
- `tests/integration/inc3/test_evaluaciones_api_integration.py` (nuevo)
- `tests/features/inc3/US-3.1.3-iniciar-evaluacion.feature` (corregido — bug de sintaxis Gherkin)
- `tests/step_defs/inc3/_auth_headers.py` (extendido — `crear_estudiante()`)
- `tests/step_defs/inc3/test_us_3_1_3_steps.py` (nuevo)

### Documentación

- `docs/plans/inc3/US-3.1.3-context.md`, `US-3.1.3-plan.md`
- `docs/reports/inc3/US-3.1.3-report.md` (este archivo)
- `quality/reports/inc3/US-3.1.3-quality.json`, `US-3.1.3-codeguard.json`, `US-3.1.3-coverage.json`
- `docs/architecture/20-context-map-integrations.md` (actualizado — relación Actividad Evaluativa → Identidad resuelta, quedaba "a definir en Incremento 3")

---

## Criterios de Aceptación (`docs/specs/inc3/US-3.1.3.md`)

- [x] Estudiante inicia su evaluación por primera vez → `Evaluacion` `EnCurso`, `preguntas_asignadas` con la cantidad exacta, evento `EvaluacionIniciada` emitido
- [x] Reconexión — idempotencia sin nuevo set → misma `Evaluacion`, mismo set, sin nuevo evento
- [x] Dos estudiantes reciben sets distintos → cada uno con su propia `Evaluacion`
- [x] Rechazo antes de la apertura → `FueraDePeriodo`
- [x] Rechazo después del cierre → `FueraDePeriodo`

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] Cierra la Iteración 1 del Incremento 3 (backend) — `US-3.1.1` → `US-3.1.2` → `US-3.1.3` completas
- [ ] Iteración 2 (`US-3.2.1` a `US-3.2.4`): `RegistrarRespuesta`, `Suspender/ReanudarEvaluacion`, `FinalizarEvaluacion`, `VerificadorDeVencimientos` — consumen el set fijado en esta US
- [ ] `docs/traceability/matrix.md` — verificar si corresponde mover algún escenario de RF-12 a *Implementado*

---

## Lecciones Aprendidas

- 💡 El event store solo indexa por `(aggregate_type, aggregate_id)` — derivar `Evaluacion.id`
  determinísticamente (`uuid5` sobre `(actividad_id, estudiante_id)`) resolvió la idempotencia
  de INV-AE-06 sin ensanchar ningún puerto ni adelantar el read model de `US-3.2.4`.
- 💡 Primera vez que el BC necesita **leer** su propio event store — el replay quedó como un
  método `reconstruir(eventos)` puro en `entities/`, reutilizable por `US-3.2.*`/`US-3.3.*`.
- ✅ `EstudianteConsultaPort` valida existencia real contra BC Identidad (a diferencia de
  `docente_headers`, que solo emite un JWT con rol sin fila en BD) — los tests de
  integración/BDD necesitaron crear un `Usuario` + `Comision` reales por cada estudiante.
- 🐛 El `.feature` de Fase 1 tenía un step Gherkin partido en dos líneas (sintaxis inválida) —
  no se detectó hasta ejecutar Fase 6; corregido ahí mismo.
- ✅ `codeguard` detectó una línea de import >100 caracteres en `src/app.py` — mismo tipo de
  hallazgo que en `US-3.1.2`, confirma que el límite real del proyecto es 100 caracteres.
- 🐛 El pre-push gate (DesignReviewer) detectó CBO=11/10 CRITICAL en `IniciarEvaluacionUseCase`
  recién al pushear — mismo patrón recurrente que `US-2.1.2`/`US-2.1.5`/`US-2.1.6`/`US-2.2.2`
  (CBO no se mide en Fase 7). Corregido moviendo la construcción de `PreguntaAsignada` a
  `Evaluacion.armar_preguntas_asignadas()` — el Use Case deja de instanciar ese Value Object
  directamente, CBO baja a 10/10 sin cambiar comportamiento.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-26
