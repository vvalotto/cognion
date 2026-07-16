# BC Notificaciones

> Rol: Generic Domain — event-driven. Responsabilidad: email en apertura/cierre de
> sesiones; extensible a otros canales.
> Detalle de mapeo RF → BC: `docs/rf/ARQ_v1.md` §mapa de BCs.

Agregados principales (ver ARQ_v1.md): `Notificación`, `Canal`, `Evento de integración`.

Se dispara por llamada directa desde Use Cases de BC Sesiones (ADR-006) — acoplamiento
consciente, documentado como deuda técnica; migrar a evento en memoria si el BC crece
(más canales, más eventos de disparo).

## Capas

Sigue la Clean Architecture del CLAUDE.md raíz: `entities/ → use_cases/ →
interface_adapters/ → frameworks/`. Reglas de imports entre capas y entre BCs: ver
CLAUDE.md raíz — no se repiten acá.

## Estado

Sin implementación — solo esqueleto de carpetas (BL-000). Primer contenido esperado en el
**Incremento 5** (`docs/rf/PLAN_v1.md` §Incremento 5), con su Iteración 0 — Modelado
(liviano) en `docs/design/domain/BC-notificaciones-modelo.md`.
