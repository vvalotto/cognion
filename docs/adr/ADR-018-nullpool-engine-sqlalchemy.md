# ADR-018 — `NullPool` en el engine async de SQLAlchemy (vs. pool con conexiones persistentes)

**Estado:** Aceptado
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
