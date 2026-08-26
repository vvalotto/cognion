# Reporte de Implementación: US-3.1.1

## Resumen Ejecutivo

- **Historia de Usuario:** US-3.1.1 — Infraestructura de Event Sourcing + CQRS del BC Actividad Evaluativa
- **Puntos estimados:** 5
- **Tiempo real:** ~13 min 35 s (suma de fases con tracking activo; PRIN-001 — tiempo real de ejecución del agente, no comparable contra estimación humana)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-26

---

## Componentes Implementados

### Entities (`src/actividad_evaluativa/entities/`)

- ✅ **`EventStorePort`** (`entities/ports/event_store_port.py`) — puerto ABC con `append`/`load`
- ✅ **`EventoParaAlmacenar`** / **`EventoAlmacenado`** — dataclasses frozen de entrada/salida del puerto
- ✅ **`ConcurrenciaOptimistaError`** (`entities/errors.py`) — excepción de infraestructura del event store

### Frameworks (`src/actividad_evaluativa/frameworks/`)

- ✅ **`EventoModel`** (`frameworks/db/models.py`) — tabla `events`, constraint única `uq_events_stream_sequence`
- ✅ **`SQLAlchemyEventStore`** (`frameworks/event_store/sqlalchemy_event_store.py`) — implementación de `EventStorePort`
- ✅ **`dependencies.py`** — composition root inicial del BC (`get_event_store`)

### Infraestructura y limpieza

- ✅ `src/sesiones/` eliminado (esqueleto vacío de BL-000, nombre pre-`ADR-015`)
- ✅ Migración `9244e3956c69_actividad_evaluativa_event_store.py` — aplicada contra la base local
- ✅ `migrations/env.py` — import de `actividad_evaluativa.frameworks.db.models` agregado a `target_metadata`

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint | 9.87/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 3 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (mín) | 72.10 | > 20 | ✅ |
| Cobertura de Tests (`entities/`) | 100% | ≥ 95% | ✅ |

**Estado General:** ✅ APROBADO (`quality/reports/inc3/US-3.1.1-quality.json`)

> `codeguard` no está instalado en este entorno local — se usó pylint + radon directamente
> (mismas herramientas que orquesta), acotado a los `.py` nuevos de `src/actividad_evaluativa/`.
> `frameworks/` está excluido del gate de coverage por `pyproject.toml` (mismo criterio en
> todos los BCs) — se valida igual de riguroso vía los 8 tests de integración contra la base
> local, no vía el porcentaje de Fase 7.

---

## Tests Implementados

### Tests Unitarios (7 tests — `tests/unit/inc3/`)

- ✅ `test_event_store_port.py` (5 tests) — `EventoParaAlmacenar`/`EventoAlmacenado`: campos, inmutabilidad, comparación por valor
- ✅ `test_errors.py` (2 tests) — `ConcurrenciaOptimistaError`: atributos y mensaje

### Tests de Integración (8 tests — `tests/integration/inc3/`)

- ✅ `test_event_store_integration.py` contra la base PostgreSQL local:
  - Append y replay de un stream nuevo, en orden
  - `load` de stream vacío devuelve lista vacía
  - Append incremental continúa la secuencia
  - Rechazo por concurrencia optimista (`ConcurrenciaOptimistaError`), sin persistir el lote en conflicto
  - Rechazo de `expected_sequence_number` distinto de 0 sobre un stream nuevo
  - Atomicidad: un lote con un evento no serializable no persiste ningún evento (incluye el válido)
  - Aislamiento entre dos streams del mismo `aggregate_type`
  - Aislamiento entre distintos `aggregate_type`

### Escenarios Gherkin de la spec (documentados, sin formalizar como `.feature` — `skip_bdd: true` por decisión de Víctor)

Los 4 escenarios de `docs/specs/inc3/US-3.1.1.md` quedan cubiertos por los tests de integración de arriba uno a uno (append/replay, concurrencia optimista, atomicidad, aislamiento).

**Todos los tests pasando:** ✅ 317/317 (suite `unit/` + `integration/` completa, sin regresiones) — 389/389 incluyendo `step_defs/` (precondición de Fase 7)

---

## Archivos Creados

### Código de Producción

- `src/actividad_evaluativa/__init__.py`, `README.md`
- `src/actividad_evaluativa/entities/__init__.py`, `errors.py`
- `src/actividad_evaluativa/entities/ports/__init__.py`, `event_store_port.py`
- `src/actividad_evaluativa/frameworks/__init__.py`, `dependencies.py`
- `src/actividad_evaluativa/frameworks/db/__init__.py`, `models.py`
- `src/actividad_evaluativa/frameworks/event_store/__init__.py`, `sqlalchemy_event_store.py`
- `migrations/versions/9244e3956c69_actividad_evaluativa_event_store.py`
- `migrations/env.py` (modificado)

### Eliminados

- `src/sesiones/` (paquete completo — esqueleto vacío de BL-000)

### Tests

- `tests/unit/inc3/test_event_store_port.py`
- `tests/unit/inc3/test_errors.py`
- `tests/integration/inc3/test_event_store_integration.py`

### Documentación

- `docs/plans/inc3/US-3.1.1-context.md`
- `docs/plans/inc3/US-3.1.1-plan.md`
- `docs/reports/inc3/US-3.1.1-report.md` (este archivo)
- `quality/reports/inc3/US-3.1.1-quality.json`

---

## Criterios de Aceptación (`docs/specs/inc3/US-3.1.1.md`)

- [x] Tabla `events` (JSONB) creada por migración, índice único `(aggregate_type, aggregate_id, sequence_number)`
- [x] `EventStorePort.append(...)` atómico — todo o nada por invocación
- [x] `EventStorePort.load(...)` devuelve el stream en orden de `sequence_number`
- [x] Rechazo por concurrencia optimista si `expected_sequence_number` no coincide
- [x] `src/sesiones/` eliminado; `src/actividad_evaluativa/` creado

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] Implementar `US-3.1.2` (Docente crea una actividad de período abierto) — consume `EventStorePort` de esta US
- [ ] Implementar `US-3.1.3` (Estudiante inicia su evaluación, set aleatorio)

---

## Lecciones Aprendidas

- 💡 El path de migraciones que la spec anticipaba (`src/actividad_evaluativa/frameworks/db/migrations/`) no existe en este proyecto — Alembic es centralizado en `migrations/` en la raíz. Corregido en el plan de implementación.
- ✅ Validar `sequence_number` con un SELECT previo (mismo patrón que `SQLAlchemyMateriaRepository.guardar`) mantuvo consistencia de estilo con el resto del código, dejando la constraint única de la tabla como respaldo ante una escritura concurrente genuina.
- ✅ `frameworks/` excluido del gate de coverage por `pyproject.toml` no significa código sin probar — los 8 tests de integración contra la base real cubren exactamente lo que el gate de coverage no mide.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-26
