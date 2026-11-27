# ADR-018 — `NullPool` en el engine async de SQLAlchemy (vs. pool con conexiones persistentes)

**Estado:** Aceptado, enmendado el 2026-11-27 (`US-12.2.5`): `NullPool` queda solo para los tests
**Fecha:** 2026-07-21

---

## Contexto

Durante la Fase 6 (Validación BDD) de `US-1.1.0`, los escenarios Gherkin necesitaban steps
asíncronos, pero `pytest-bdd` (versión instalada, 8.1.0) no soporta step functions `async def`
— las invoca de forma síncrona sin awaitear la corrutina. La solución fue ejecutar el cuerpo de
cada step vía `asyncio.run()`, lo cual crea y cierra un event loop nuevo por step. El engine
compartido de `src/shared/frameworks/db.py` (`ADR-017`) usaba el pool por defecto de SQLAlchemy
(`AsyncAdaptedQueuePool`), que retiene conexiones `asyncpg` entre usos — una conexión creada en
el loop del step N quedaba inválida al reutilizarse en el loop del step N+1, produciendo
`RuntimeError: ... attached to a different loop`.

## Opciones Consideradas

- **Engine separado con `NullPool` solo para tests BDD** (dependency override del ASGI
  transport) — descartada: agrega infraestructura de test (override de dependencies, engine
  paralelo) para un problema que en producción también podría manifestarse bajo ciertos
  escenarios de despliegue (múltiples workers/procesos reiniciando conexiones), sin aportar
  garantía adicional real.
- **`NullPool` en el engine compartido de producción y test** — elegida.

## Decisión

El engine compartido (`src/shared/frameworks/db.py`) usa `poolclass=NullPool`: cada operación
de base de datos abre y cierra su propia conexión `asyncpg`, sin pool de conexiones persistente.

## Justificación

Para la escala del proyecto (30–60 alumnos por comisión, uso académico no concurrente a gran
volumen) el costo de abrir una conexión `asyncpg` nueva por operación es despreciable
(sub-milisegundo en local, bajo en la topología de despliegue prevista). A cambio, se elimina
de raíz una clase entera de bugs de "event loop cruzado" — no solo en los steps BDD actuales,
sino en cualquier test o entorno futuro que ejecute operaciones de DB en loops de asyncio
distintos dentro del mismo proceso.

## Impacto en Configuración

- `src/shared/frameworks/db.py` — `create_async_engine(..., poolclass=NullPool)`.

## Consecuencias

- ✅ Elimina los bugs de "conexión atada a un loop distinto" en tests BDD (`asyncio.run()` por
  step) y en cualquier escenario futuro con múltiples loops en el mismo proceso.
- ✅ Sin pool que gestionar/monitorear — menos superficie operativa para un equipo unipersonal.
- ⚠️ Sin reutilización de conexiones: cada operación paga el costo de handshake TCP/auth de
  PostgreSQL. Aceptable a esta escala; **revisar si el proyecto crece a un volumen de tráfico
  donde el overhead de conexión se vuelva medible.**

---

## Enmienda 2026-11-27 (`US-12.2.5`, hallazgo `IM-06`)

`NullPool` se adoptó por una necesidad de los **tests**: cada paso del BDD corre con `asyncio.run()` y `pytest-asyncio` abre un loop por test, así que una conexión de `asyncpg` queda atada al loop que la creó. En ejecución hay un solo proceso y un solo loop, y ese problema no existe. Dejar `NullPool` ahí costaba una conexión nueva por operación: con 60 alumnos respondiendo a la vez, 60 conexiones simultáneas y 60 negociaciones.

**Decisión:** el motor se arma desde la configuración (`crear_motor` de `src/shared/frameworks/db.py`).

- **En ejecución, pool de conexiones** (`DB_POOL=cola`, el valor por defecto): `db_pool_size=10`, `db_max_overflow=20`, `db_pool_timeout=30` y `pool_pre_ping`. Como mucho 30 conexiones por proceso.
- **En los tests, `NullPool`** (`DB_POOL=nula`, que fija `tests/conftest.py` antes de importar `src.settings`).
- `max_connections=100` de PostgreSQL se mantiene como margen; solo cambian los comentarios que lo justificaban por `NullPool`.

**Medición (local, 2026-11-27, 60 operaciones a la vez, PostgreSQL de la Mac):** mediana de una operación 14 ms con `NullPool` y 1,5 ms con pool; las 60 a la vez terminan en ~250 ms contra ~114 ms, y la peor operación pasa de ~190–220 ms a ~83–87 ms. El costo en el servidor sigue sin medirse (Issue #624).

**Restricción:** el pool vale con **un solo proceso** (`docs/INSTALACION.md`). Con más de un proceso cada uno tendría su pool y la suma podría pasar `max_connections`; además el canal de la sesión en vivo ya exige un solo proceso (`IM-05`).
