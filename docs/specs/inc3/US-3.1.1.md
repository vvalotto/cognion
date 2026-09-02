# US-3.1.1: Infraestructura de Event Sourcing + CQRS del BC Actividad Evaluativa

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-3.1`
**Tipo**: `infra backend` (técnica — sin comando de negocio propio)
**Agregado principal afectado**: — (infraestructura transversal al BC)
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **equipo de desarrollo**,
quiero **la infraestructura de event store append-only y el mecanismo de append/replay que
`ADR-002` decidió para este BC**
para **que `US-3.1.2` y `US-3.1.3` (y toda la Iteración 2 y 3) tengan dónde persistir sus
eventos de dominio, sin que cada Use Case reinvente su propia transacción**.

---

## Contexto del dominio

### Problema

Identidad y Banco de Preguntas usan repositorios CRUD estándar (`ADR-004`, PostgreSQL +
SQLAlchemy async) — no existe todavía infraestructura de event store reutilizable. Este es el
primer BC del proyecto con Event Sourcing + CQRS (`ADR-002`), y el modelo de dominio
(`BC-actividad-evaluativa-modelo.md` §6) ya definió el diseño concreto que esta US construye:
tabla única `events`, stream por `(aggregate_type, aggregate_id)`, concurrencia optimista por
`sequence_number`.

Además, `src/sesiones/` es hoy solo el esqueleto de carpetas vacío de BL-000 (`README.md`:
"Sin implementación — solo esqueleto de carpetas"), con el nombre anterior al renombre de
`ADR-015`. Esta US también resuelve esa deuda: el paquete nuevo se crea directamente como
`src/actividad_evaluativa/`, y el esqueleto de `src/sesiones/` se elimina — nunca tuvo código de
negocio, no hay nada que migrar.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Tabla | `events` (JSONB, PostgreSQL) | Columnas: `id` (PK), `aggregate_type` (`"ActividadEvaluativaPeriodoAbierto"` \| `"Evaluacion"`), `aggregate_id` (UUID), `sequence_number` (int), `event_type` (str), `payload` (JSONB), `occurred_at` (timestamptz) |
| Port (nuevo) | `EventStorePort` | `append(aggregate_type, aggregate_id, expected_sequence_number, events)`, `load(aggregate_type, aggregate_id)` — definido en `entities/ports/`, sin conocer SQLAlchemy |
| Adapter (nuevo) | `SQLAlchemyEventStore` | Implementa `EventStorePort` sobre la sesión async compartida (`shared/frameworks/db.py`, `ADR-017`) |
| Excepción de infraestructura | `ConcurrenciaOptimistaError` | `append` la lanza si `sequence_number` esperado no coincide con el último persistido del stream — evita que un doble submit (ej. reintento de red del estudiante) duplique un evento |

---

## Especificacion del comportamiento

### Precondicion

- Ninguna — es el primer código del BC. No depende de ninguna otra US de Actividad Evaluativa.

### Postcondicion

- Tabla `events` creada por migración Alembic, con índice sobre `(aggregate_type, aggregate_id,
  sequence_number)` para soportar el replay ordenado de un stream.
- `EventStorePort.append(...)` persiste los eventos de una invocación en una única transacción
  (`ADR-009`) — si la lista tiene más de un evento (no ocurre todavía en Iteración 1, sí en
  `US-3.1.1`+`US-3.2.4`/`US-3.3.2` más adelante), se persisten todos o ninguno.
- `EventStorePort.load(aggregate_type, aggregate_id)` devuelve la lista de eventos del stream en
  orden de `sequence_number`, lista para que el aggregate correspondiente reconstruya su estado
  (`replay`) — nunca lee el stream de otro aggregate.
- `src/sesiones/` eliminado; `src/actividad_evaluativa/` creado con las 4 capas
  (`entities/use_cases/interface_adapters/frameworks`) y `EventStorePort` como primer contenido
  real de `entities/ports/`.
- Un test de integración prueba el ciclo completo `append` → `load` → replay con un aggregate de
  ejemplo mínimo (fixture de test, no un aggregate de negocio real — `US-3.1.2`/`US-3.1.3`
  proveen los primeros aggregates reales).

### Invariantes

| ID | Invariante |
|----|------------|
| — | `sequence_number` estrictamente creciente y sin huecos dentro de un mismo stream `(aggregate_type, aggregate_id)` — lo garantiza el propio `EventStorePort.append`, no el llamador. |
| — | `append` es atómico: ante cualquier excepción durante la escritura, no queda ningún evento parcial persistido de esa invocación (`ADR-009`). |
| — | Un stream nunca se lee cruzado con otro — `load` siempre filtra por `(aggregate_type, aggregate_id)` exacto (`BC-actividad-evaluativa-modelo.md` §6, "nunca se lee el stream de otro aggregate"). |

---

## Criterios de aceptacion

```gherkin
Feature: Infraestructura de event store append-only (US-3.1.1)

  Scenario: Append y replay de un stream nuevo
    Given un stream vacío para (aggregate_type="EjemploTest", aggregate_id=<uuid>)
    When se hace append de 3 eventos con sequence_number 1, 2, 3
    And luego se hace load de ese mismo stream
    Then el resultado devuelve los 3 eventos en orden de sequence_number

  Scenario: Rechazo por concurrencia optimista
    Given un stream con el último evento en sequence_number=2
    When se intenta append con expected_sequence_number=1 (desactualizado)
    Then el sistema rechaza la operación con ConcurrenciaOptimistaError
    And no se persiste ningún evento nuevo

  Scenario: Atomicidad del append múltiple
    Given un Use Case que produce 2 eventos en la misma invocación
    When ocurre una excepción de dominio después de preparar el primer evento pero antes de
      persistir el segundo
    Then no queda ningún evento de esa invocación persistido en la tabla events

  Scenario: Aislamiento entre streams
    Given dos streams distintos, cada uno con sus propios eventos
    When se hace load de uno de los dos
    Then el resultado no incluye ningún evento del otro stream
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — implementa el diseño ya decidido en `ADR-002` (Event Sourcing + CQRS) y detallado en
  `BC-actividad-evaluativa-modelo.md` §6. No introduce una decisión nueva, solo la construye.

**Capa(s) afectadas:**
- [x] Entities — `EventStorePort` (`entities/ports/`), `ConcurrenciaOptimistaError`
  (`entities/errors.py`)
- [ ] Use Cases — sin Use Case propio (lo consumen `US-3.1.2`/`US-3.1.3` en adelante)
- [ ] Interface Adapters — sin controller propio (infraestructura pura)
- [x] Frameworks — `SQLAlchemyEventStore`, modelo SQLAlchemy `EventoORM` (tabla `events`),
  migración Alembic
- [ ] Frontend — no aplica a esta iteración (diferido a `US-3.4.1`, Iteración 4)

---

## Fuente de verdad UX

No aplica — infraestructura backend pura, sin pantalla.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/sesiones/` | Eliminado — esqueleto vacío de BL-000, nombre anterior a `ADR-015` |
| `src/actividad_evaluativa/__init__.py` | Paquete nuevo |
| `src/actividad_evaluativa/entities/ports/event_store_port.py` | `EventStorePort` (interfaz `append`/`load`) |
| `src/actividad_evaluativa/entities/errors.py` | `ConcurrenciaOptimistaError` |
| `src/actividad_evaluativa/frameworks/db/models.py` | Modelo SQLAlchemy `EventoORM` (tabla `events`) |
| `src/actividad_evaluativa/frameworks/db/migrations/` | Migración Alembic — crea tabla `events` + índice `(aggregate_type, aggregate_id, sequence_number)` |
| `src/actividad_evaluativa/frameworks/event_store/sqlalchemy_event_store.py` | Implementación de `EventStorePort` sobre `shared/frameworks/db.py` |
| `src/actividad_evaluativa/frameworks/dependencies.py` | Composition root del BC (arranca vacío, lo completan `US-3.1.2`/`US-3.1.3`) |
| `tests/unit/inc3/test_event_store.py` | Tests de append/replay/concurrencia con aggregate de ejemplo |

---

## Referencias

- Modelo de dominio: `docs/design/domain/BC-actividad-evaluativa-modelo.md` §6 (diseño del event
  store), §2 (dos aggregates, un stream cada uno)
- Decisiones: `ADR-002` (Event Sourcing + CQRS), `ADR-009` (Unit of Work por Use Case),
  `ADR-004` (PostgreSQL + SQLAlchemy async), `ADR-015` (renombre del BC), `ADR-017`
  (`shared/frameworks/db.py`)
- Consumida por: `US-3.1.2`, `US-3.1.3` y toda la Iteración 2 y 3
- Candidatas: `docs/plans/inc3/inc3-candidatas.md`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
