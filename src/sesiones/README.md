# BC Sesiones

> Rol: Core Domain — Event Sourcing + CQRS (ADR-002). Responsabilidad: ciclo de vida de
> sesiones en vivo y de período abierto; ranking; persistencia de respuestas.
> Detalle de mapeo RF → BC: `docs/rf/ARQ_v1.md` §mapa de BCs.

Agregados principales (ver ARQ_v1.md): `Sesión`, `PreguntaAsignada`, `Respuesta`,
`Ranking`, `SesiónEnVivo`, `SesiónPeríodoAbierto`.

Persistencia: event store append-only (tabla PostgreSQL JSONB) — no CRUD directo sobre el
agregado. Ver ADR-002 y ADR-009 (Unit of Work / transaccionalidad).

## Capas

Sigue la Clean Architecture del CLAUDE.md raíz: `entities/ → use_cases/ →
interface_adapters/ → frameworks/`. Reglas de imports entre capas y entre BCs: ver
CLAUDE.md raíz — no se repiten acá. Integración con BC Notificaciones: llamada directa
entre Use Cases (deuda técnica consciente, ver ADR-006) — nunca import directo entre BCs.

## Estado

Sin implementación — solo esqueleto de carpetas (BL-000). Primer contenido esperado en el
**Incremento 3** (`docs/rf/PLAN_v1.md` §Incremento 3), con su Iteración 0 — Modelado en
`docs/design/domain/BC-sesiones-modelo.md`.
