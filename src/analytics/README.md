# BC Analytics

> Rol: Supporting Domain — Read Models (solo lectura). Responsabilidad: proyecciones desde
> el event store de BC Sesiones; métricas de uso.
> Detalle de mapeo RF → BC: `docs/rf/ARQ_v1.md` §mapa de BCs.

Agregados principales (ver ARQ_v1.md): `ReadModel`, `Proyección`, `MétricaDeSesión`.

Este BC no origina eventos propios — proyecta desde el event store de `src/sesiones/`.
No implica import directo entre BCs: la proyección consume el event store a través de un
puerto, igual que cualquier otra integración entre BCs.

## Capas

Sigue la Clean Architecture del CLAUDE.md raíz: `entities/ → use_cases/ →
interface_adapters/ → frameworks/`. Reglas de imports entre capas y entre BCs: ver
CLAUDE.md raíz — no se repiten acá.

## Estado

Sin implementación — solo esqueleto de carpetas (BL-000). Primer contenido esperado en el
**Incremento 4** (`docs/rf/PLAN_v1.md` §Incremento 4), con su Iteración 0 — Modelado
(liviano) en `docs/design/domain/BC-analytics-modelo.md`.
