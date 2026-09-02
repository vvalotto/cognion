# Reporte de Implementación: US-3.1.2

## Resumen Ejecutivo

- **Historia de Usuario:** US-3.1.2 — Docente crea una actividad de período abierto
- **Puntos estimados:** 5
- **Tiempo real:** ~19 min (suma de fases con tracking activo; PRIN-001 — tiempo real de ejecución del agente, no comparable contra estimación humana)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-26

---

## Componentes Implementados

### Entities (`src/actividad_evaluativa/entities/`)

- ✅ **`ActividadEvaluativaPeriodoAbierto`** (`entities/actividad_evaluativa_periodo_abierto.py`) — aggregate root, factory `crear()` valida INV-AE-02/03
- ✅ **`ActividadEvaluativaCreada`** (`entities/eventos.py`) — primer evento de dominio del BC
- ✅ **`MateriaNoExiste`, `PreguntasInsuficientes`, `PeriodoInvalido`, `CantidadIntentosInvalida`** (`entities/errors.py`) — errores de dominio, agregados al archivo de errores de infraestructura de `US-3.1.1`
- ✅ **`PreguntaConsultaPort`** (`entities/ports/pregunta_consulta_port.py`) — puerto hacia Banco de Preguntas, conteo de preguntas activas (INV-AE-01)
- ✅ **`MateriaConsultaPort` / `MateriaDTO`** (`entities/ports/materia_consulta_port.py`) — puerto hacia Banco de Preguntas, validación de existencia

### Use Cases (`src/actividad_evaluativa/use_cases/`)

- ✅ **`CrearActividadPeriodoAbiertoUseCase`** — orquesta INV-AE-01/02/03, arma `ActividadEvaluativaCreada`, invoca `EventStorePort.append` (`US-3.1.1`)

### Interface Adapters (`src/actividad_evaluativa/interface_adapters/`)

- ✅ **`ActividadesController`** — adapta requests HTTP al use case

### Frameworks (`src/actividad_evaluativa/frameworks/`)

- ✅ **`MateriaConsultaPortInProcess`** / **`PreguntaConsultaPortInProcess`** (`frameworks/adapters/`) — mismo patrón de `US-2.1.2` (Identidad→Banco de Preguntas), llamada in-process sin FK entre esquemas
- ✅ **`schemas.py`** — `CrearActividadRequest`/`ActividadResponse` (Pydantic)
- ✅ **`actividades_router.py`** — `POST /actividades` (rol `docente`), mapea `MateriaNoExiste`→404, resto de errores de dominio→422
- ✅ **`dependencies.py`** (extendido) — `get_actividades_controller`, `require_docente`
- ✅ `src/app.py` — `actividades_router` registrado

---

## API Endpoints

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| POST | `/actividades` | Crea una actividad de período abierto | ✅ rol `docente` |

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint | 9.59/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 4 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (mín) | 72.33 | > 20 | ✅ |
| Cobertura de Tests (`entities/`+`use_cases/`+`interface_adapters/`) | 100% | ≥ 95% | ✅ |

**Estado General:** ✅ APROBADO (`quality/reports/inc3/US-3.1.2-quality.json`)

> `codeguard` sobre los 18 `.py` nuevos/modificados de la US: 0 errores, 0 warnings, 54 infos
> (`quality/reports/inc3/US-3.1.2-codeguard.json`). `frameworks/` excluido del gate de coverage
> por `pyproject.toml` (mismo criterio en todos los BCs) — cubierto en cambio por 7 tests de
> integración HTTP y 5 escenarios BDD contra la base local.

---

## Tests Implementados

### Tests Unitarios (24 tests — `tests/unit/inc3/`)

- ✅ `test_actividad_evaluativa_periodo_abierto.py` (7 tests) — factory `crear()`: caso válido, IDs distintos, INV-AE-02/03
- ✅ `test_crear_actividad_periodo_abierto_use_case.py` (5 tests) — los 5 escenarios de la spec, con fakes en memoria de los 3 puertos
- ✅ `test_actividades_controller.py` (1 test) — delegación al use case
- ✅ `test_errors.py` (extendido, +8 tests) — los 4 errores de dominio nuevos

### Tests de Integración (15 tests — `tests/integration/inc3/`)

- ✅ `test_actividades_api_integration.py` (7 tests) — `POST /actividades` contra la base PostgreSQL local vía HTTP real: creación válida, los 4 rechazos de dominio, 401 sin auth, 403 con rol insuficiente
- ✅ `test_event_store_integration.py` (8 tests, `US-3.1.1`, sin cambios) — regresión verificada

### Escenarios BDD (5 escenarios — `tests/features/inc3/US-3.1.2-crear-actividad-periodo-abierto.feature`)

- ✅ Docente crea una actividad válida
- ✅ Rechazo por preguntas insuficientes
- ✅ Rechazo por período inválido
- ✅ Rechazo por cantidad de intentos inválida
- ✅ Rechazo por materia inexistente

**Todos los tests pasando:** ✅ 418/418 (suite completa `unit/` + `integration/` + `step_defs/`, sin regresiones)

---

## Archivos Creados

### Código de Producción

- `src/actividad_evaluativa/entities/actividad_evaluativa_periodo_abierto.py`
- `src/actividad_evaluativa/entities/eventos.py`
- `src/actividad_evaluativa/entities/errors.py` (extendido)
- `src/actividad_evaluativa/entities/ports/materia_consulta_port.py`
- `src/actividad_evaluativa/entities/ports/pregunta_consulta_port.py`
- `src/actividad_evaluativa/use_cases/__init__.py`, `crear_actividad_periodo_abierto.py`
- `src/actividad_evaluativa/interface_adapters/__init__.py`
- `src/actividad_evaluativa/interface_adapters/controllers/__init__.py`, `actividades_controller.py`
- `src/actividad_evaluativa/frameworks/adapters/__init__.py`, `materia_consulta_port_in_process.py`, `pregunta_consulta_port_in_process.py`
- `src/actividad_evaluativa/frameworks/api/__init__.py`, `schemas.py`, `actividades_router.py`
- `src/actividad_evaluativa/frameworks/dependencies.py` (extendido)
- `src/app.py` (modificado — registro del router)

### Tests

- `tests/unit/inc3/_fakes.py`, `test_actividad_evaluativa_periodo_abierto.py`, `test_crear_actividad_periodo_abierto_use_case.py`, `test_actividades_controller.py`
- `tests/unit/inc3/test_errors.py` (extendido)
- `tests/integration/inc3/conftest.py`, `test_actividades_api_integration.py`
- `tests/features/inc3/US-3.1.2-crear-actividad-periodo-abierto.feature`
- `tests/step_defs/inc3/__init__.py`, `_auth_headers.py`, `test_us_3_1_2_steps.py`

### Documentación

- `docs/plans/inc3/US-3.1.2-context.md`, `US-3.1.2-plan.md`
- `docs/reports/inc3/US-3.1.2-report.md` (este archivo)
- `quality/reports/inc3/US-3.1.2-quality.json`, `US-3.1.2-codeguard.json`
- `docs/architecture/20-context-map-integrations.md` (actualizado — relación Actividad Evaluativa→Banco de Preguntas ratificada)

---

## Criterios de Aceptación (`docs/specs/inc3/US-3.1.2.md`)

- [x] Docente crea una actividad válida → `ActividadEvaluativaPeriodoAbierto` persistida con `cerrada_manualmente=false`, evento `ActividadEvaluativaCreada` emitido
- [x] Rechazo por preguntas insuficientes → `PreguntasInsuficientes`, ninguna actividad persistida
- [x] Rechazo por período inválido → `PeriodoInvalido`
- [x] Rechazo por cantidad de intentos inválida → `CantidadIntentosInvalida`
- [x] Rechazo por materia inexistente → `MateriaNoExiste`

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] Implementar `US-3.1.3` (Estudiante inicia su evaluación — set aleatorio de preguntas, RF-12) — consume la actividad creada en esta US
- [ ] `US-3.3.1`/`US-3.3.2` (Iteración 3) modificarán/cerrarán esta misma `ActividadEvaluativaPeriodoAbierto`

---

## Lecciones Aprendidas

- ✅ El patrón de puerto + adapter in-process de `US-2.1.2` (`MateriaPort`) se reutilizó sin
  cambios de diseño para `MateriaConsultaPort`/`PreguntaConsultaPort` — tercera vez que se aplica
  el mismo patrón de integración entre BCs sin imports directos.
- ✅ `ListarMateriasUseCase` (`US-2.1.9`) fue la referencia exacta para contar preguntas activas
  de una materia sin ensanchar `PreguntaRepositoryPort`.
- 💡 El límite de línea real del proyecto es 100 caracteres (`pyproject.toml`/`.pylintrc`), no
  120 como sugiere el template genérico de Fase 0 del skill — `codeguard` lo detectó en 3
  docstrings largos, corregidos antes de cerrar Fase 7.
- ✅ Sin CRITICAL de CBO en `ActividadesController` (a diferencia del patrón repetido en
  `PreguntasController` de `US-2.1.2`/`US-2.1.5`/`US-2.1.6`) — el problema de CBO alto aparece
  recién cuando un controller acumula 4-5 use cases inyectados; esta US solo inyecta uno.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-26
