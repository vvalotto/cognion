# ADR-004 — PostgreSQL como base de datos (vs. SQLite)

**Estado:** Aceptado
**Fecha:** 2026-07-08

---

## Contexto

El sistema necesita soportar hasta 60 alumnos confirmando respuestas simultáneamente en
sesiones de período abierto. El event store requiere escrituras append-only frecuentes. El
hosting es Fly.io.

## Opciones Consideradas

- **SQLite** — permite un único escritor a la vez. Descartada: con 60 respuestas simultáneas en
  período abierto, la contención de escritura es un riesgo real contra el driver 2
  (persistencia atómica).
- **PostgreSQL** — maneja escrituras concurrentes correctamente, con soporte JSONB para los
  payloads del event store. Elegida.

## Decisión

PostgreSQL como única base de datos. El event store es una tabla append-only dentro de la misma
instancia PostgreSQL.

## Justificación

PostgreSQL maneja escrituras concurrentes sin la contención que SQLite tendría a esta escala.
Fly.io ofrece PostgreSQL administrado, eliminando el overhead de operación. El soporte JSONB de
PostgreSQL es ideal para los payloads del event store.

## Impacto en Configuración

- `docker-compose.yml` — servicio `postgres` para desarrollo local.
- `.env.example` — variable `DATABASE_URL` con driver async (`asyncpg`).
- `pyproject.toml` — dependencias `sqlalchemy[asyncio]`, `asyncpg`, `alembic`.
- `alembic.ini` / `migrations/` — configurado contra PostgreSQL, no SQLite.

## Consecuencias

- ✅ Escrituras concurrentes sin contención
- ✅ JSONB para payloads del event store (consultable e indexable)
- ✅ Fly.io Postgres administrado sin overhead de operación
- ⚠️ Ligeramente más complejo de configurar localmente que SQLite (mitigado con Docker Compose)
