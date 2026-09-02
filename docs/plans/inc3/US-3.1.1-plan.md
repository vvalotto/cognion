# Plan de Implementación: US-3.1.1 - Infraestructura de Event Sourcing + CQRS del BC Actividad Evaluativa

**Patrón:** Clean Architecture BC-first (`entities → use_cases → interface_adapters → frameworks`)
**Producto:** cognion
**Estado:** ✅ COMPLETADO

## Métricas de Tiempo (tracking real, `.claude/tracking/US-3.1.1-tracking.json`)

| Fase | Tiempo real |
|---|---|
| 0 — Validación de Contexto | 4min 23s |
| 2 — Plan de Implementación | 59s |
| 3 — Implementación Guiada por Tareas | 4min 10s |
| 4 — Tests Unitarios | 41s |
| 5 — Tests de Integración | 1min 16s |
| 7 — Quality Gates | 3min 06s |
| 8 — Documentación | — |

> Nota (PRIN-001, `skill.md`): estos son tiempos reales de ejecución del agente, no
> comparables contra una estimación humana en story points — no se calcula varianza.

## Lecciones Aprendidas

- 💡 El path de migraciones que la spec anticipaba
  (`src/actividad_evaluativa/frameworks/db/migrations/`) no existe en este proyecto — Alembic
  es centralizado en `migrations/` en la raíz. Se corrigió en el plan sin tocar la spec (mismo
  tipo de ajuste menor ya visto en otras US de este proyecto).
- ✅ La decisión de no capturar `IntegrityError` y en cambio validar `sequence_number` con un
  SELECT previo (mismo patrón que `SQLAlchemyMateriaRepository.guardar`) mantuvo consistencia
  de estilo con el resto del código — la constraint única de la tabla queda como respaldo, no
  como mecanismo primario de detección.
- ✅ `frameworks/` está excluido del gate de cobertura por `pyproject.toml` — el event store se
  valida igual de riguroso, pero vía los tests de integración (Fase 5) contra la base local, no
  vía el porcentaje de Fase 7.

## Componentes a Implementar

### 0. Limpieza previa
- [x] Eliminar `src/sesiones/` — esqueleto vacío de BL-000 (nombre pre-`ADR-015`, sin código de
  negocio, nada que migrar)

### 1. Entities (`src/actividad_evaluativa/entities/`)
- [x] `src/actividad_evaluativa/__init__.py`
  - Paquete nuevo del BC
- [x] `src/actividad_evaluativa/entities/__init__.py`
- [x] `src/actividad_evaluativa/entities/errors.py`
  - `ConcurrenciaOptimistaError` — excepción de infraestructura (no de dominio), la lanza
    `EventStorePort.append` si `expected_sequence_number` no coincide con el último persistido
- [x] `src/actividad_evaluativa/entities/ports/__init__.py`
- [x] `src/actividad_evaluativa/entities/ports/event_store_port.py`
  - `EventStorePort` (ABC): `append(aggregate_type, aggregate_id,
    expected_sequence_number, events) -> None`, `load(aggregate_type, aggregate_id) ->
    list[EventoAlmacenado]`
  - `EventoParaAlmacenar` (dataclass de entrada de `append`) y `EventoAlmacenado` (dataclass
    de retorno de `load`): `sequence_number`, `event_type`, `payload`, `occurred_at` — sin
    depender de SQLAlchemy en `entities/`

### 2. Frameworks — persistencia (`src/actividad_evaluativa/frameworks/`)
- [x] `src/actividad_evaluativa/frameworks/__init__.py`
- [x] `src/actividad_evaluativa/frameworks/db/__init__.py`
- [x] `src/actividad_evaluativa/frameworks/db/models.py`
  - `EventoORM` (hereda de `src.shared.frameworks.db.Base`) — tabla `events`: `id` (PK, UUID),
    `aggregate_type` (String), `aggregate_id` (UUID), `sequence_number` (Integer),
    `event_type` (String), `payload` (JSONB), `occurred_at` (DateTime timezone=True)
  - Índice único `(aggregate_type, aggregate_id, sequence_number)` — sostiene el replay
    ordenado y ayuda a detectar colisiones de concurrencia a nivel de base
- [x] `src/actividad_evaluativa/frameworks/event_store/__init__.py`
- [x] `src/actividad_evaluativa/frameworks/event_store/sqlalchemy_event_store.py`
  - `SQLAlchemyEventStore(EventStorePort)` — recibe `AsyncSession` inyectada (mismo patrón que
    los repositorios de Banco de Preguntas/Identidad)
  - `append`: SELECT del último `sequence_number` del stream con lock adecuado (`FOR UPDATE`
    o comparación optimista simple según se resuelva en Fase 3), compara contra
    `expected_sequence_number`, inserta filas nuevas con `sequence_number` consecutivo, deja
    el commit a cargo del llamador (`ADR-009`, la sesión ya viene con su propio ciclo de vida)
  - `load`: SELECT ordenado por `sequence_number` filtrando por `(aggregate_type,
    aggregate_id)`, mapea `EventoORM` → `EventoAlmacenado`
- [x] `src/actividad_evaluativa/frameworks/dependencies.py`
  - Composition root del BC — por ahora solo expone `get_event_store` (provider FastAPI-style,
    `Depends(get_session)` + `SQLAlchemyEventStore`); lo completan `US-3.1.2`/`US-3.1.3` con
    sus propios use cases y controllers

### 3. Integración con Alembic
- [x] `migrations/env.py` — agregado el import de
  `src.actividad_evaluativa.frameworks.db.models` (mismo patrón que `banco_preguntas`/
  `identidad`), para que `target_metadata` incluya `EventoModel`
- [x] Migración `9244e3956c69_actividad_evaluativa_event_store.py` (autogenerada, revisada a
  mano) — crea la tabla `events` + `uq_events_stream_sequence`. Aplicada contra la base local.

**Estado:** 12/12 tareas completadas

---

## Fuera de esta US (a cargo de US-3.1.2/US-3.1.3)

- Cualquier aggregate de negocio real (`ActividadEvaluativaPeriodoAbierto`, `Evaluacion`)
- Cualquier endpoint FastAPI / router — esta US no expone HTTP todavía
- El mecanismo de replay hacia un aggregate concreto (`from_events(...)`) — esta US entrega el
  event store genérico; reconstruir un aggregate específico es responsabilidad de cada aggregate,
  no del event store

## Notas de implementación

- **Concurrencia optimista:** el mecanismo exacto (constraint único en base vs. verificación en
  aplicación antes del insert) se decide en Fase 3, ambos cumplen el criterio de aceptación de
  la spec; preferencia por el constraint único de base (`(aggregate_type, aggregate_id,
  sequence_number)`) porque no depende de una lectura previa dentro de la misma transacción.
- **Test de integración con aggregate de ejemplo:** no es un aggregate de negocio — un
  fixture mínimo de test (ej. `aggregate_type="EjemploTest"`) que ejercita el ciclo completo
  append→load sin acoplar el test a `US-3.1.2`/`US-3.1.3`, que todavía no existen.
