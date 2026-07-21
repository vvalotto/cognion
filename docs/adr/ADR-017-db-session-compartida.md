# ADR-017 — Engine y sesión async de SQLAlchemy compartidos en `src/shared/frameworks/db.py` (vs. uno por BC)

**Estado:** Aceptado
**Fecha:** 2026-07-21

---

## Contexto

`US-1.1.0` es la primera US que introduce persistencia real (SQLAlchemy async + PostgreSQL,
`ADR-004`) en un BC. `CLAUDE.md` define `shared/entities/` como la única excepción transversal
a la regla de no-imports-entre-BC, pero no dice nada sobre infraestructura técnica pura (engine,
sesión, `Base` declarativa) que todos los BC necesitan por igual para hablar con la misma
instancia de PostgreSQL.

## Opciones Consideradas

- **Un engine y una `Base` declarativa por BC** (cada `frameworks/db/` arma su propio
  `create_async_engine`) — descartada: duplica pools de conexión contra la misma base de datos
  para cada BC, sin ningún beneficio de aislamiento real (todos apuntan a la misma instancia
  PostgreSQL, `ADR-004`), y obliga a Alembic a combinar múltiples `Base.metadata` en
  `migrations/env.py` de forma más enrevesada.
- **`src/shared/frameworks/db.py`** — elegida.

## Decisión

Un único engine async, `async_sessionmaker` y `Base` declarativa viven en
`src/shared/frameworks/db.py`. Cada BC importa `Base` desde ahí para sus modelos ORM, y
`get_session()` como dependency de FastAPI para sus repositorios.

## Justificación

`shared/entities/` ya reconoce que hay utilidades transversales sin lógica de negocio de un BC
específico — el engine/sesión de base de datos es exactamente ese tipo de utilidad, solo que en
la capa `frameworks` en lugar de `entities`. Un solo pool de conexiones es más simple de operar
y monitorear para un equipo unipersonal, y no compromete el aislamiento de dominio: los BC
siguen sin poder importarse entre sí, solo comparten la plomería de acceso a datos.

## Impacto en Configuración

- `src/shared/frameworks/db.py` — nuevo módulo, `Base`, `engine`, `SessionLocal`,
  `get_session()`.
- `migrations/env.py` — `target_metadata` apunta a `Base.metadata`; cada BC con modelos ORM
  debe importarse ahí (aunque sea solo por side-effect de registro) para que Alembic los vea.

## Consecuencias

- ✅ Un solo pool de conexiones para toda la app — más simple de operar.
- ✅ `migrations/env.py` combina el esquema de todos los BC sin lógica adicional de merge de
  metadata.
- ⚠️ `src/shared/frameworks/` es una excepción nueva no prevista literalmente en `CLAUDE.md`
  (que solo menciona `shared/entities/`) — a diferenciar de lógica de negocio compartida, que
  sigue prohibida entre BC.
