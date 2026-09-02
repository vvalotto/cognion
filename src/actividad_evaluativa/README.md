# BC Actividad Evaluativa

> Rol: Core Domain — Event Sourcing + CQRS (`ADR-002`). Responsabilidad: ciclo de vida de
> actividades de período abierto y de las evaluaciones que rinde cada estudiante.
> Detalle de mapeo RF → BC: `docs/rf/ARQ_v1.md` §mapa de BCs. Renombrado desde "Sesiones"
> por `ADR-015`.

Agregados principales (ver `docs/design/domain/BC-actividad-evaluativa-modelo.md`):
`ActividadEvaluativaPeriodoAbierto`, `Evaluacion` — dos aggregates independientes, cada uno
con su propio stream de eventos (§2 del modelo).

## Capas

Sigue la Clean Architecture del `CLAUDE.md` raíz: `entities/ → use_cases/ →
interface_adapters/ → frameworks/`. Reglas de imports entre capas y entre BCs: ver
`CLAUDE.md` raíz — no se repiten acá.

Persistencia: event store append-only (tabla `events`, PostgreSQL JSONB) — no CRUD directo
sobre los aggregates. Ver `ADR-002` y `ADR-009` (Unit of Work / transaccionalidad).

## Estado

Infraestructura de Event Sourcing + CQRS implementada (`US-3.1.1`) — `EventStorePort`,
`SQLAlchemyEventStore`, tabla `events`. Primer aggregate de negocio
(`ActividadEvaluativaPeriodoAbierto`) en `US-3.1.2`.
