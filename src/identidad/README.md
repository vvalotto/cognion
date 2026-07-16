# BC Identidad

> Rol: Generic Domain. Responsabilidad: usuarios, roles, credenciales, JWT.
> Detalle de mapeo RF → BC: `docs/rf/ARQ_v1.md` §mapa de BCs.

Agregados principales (ver ARQ_v1.md): `Usuario`, `Rol`, `Credencial`, `Token`.

## Capas

Sigue la Clean Architecture del CLAUDE.md raíz: `entities/ → use_cases/ →
interface_adapters/ → frameworks/`. Reglas de imports entre capas y entre BCs: ver
CLAUDE.md raíz — no se repiten acá.

## Estado

Sin implementación — solo esqueleto de carpetas (BL-000). Primer contenido esperado en el
**Incremento 1** (`docs/rf/PLAN_v1.md` §Incremento 1), con su Iteración 0 — Modelado en
`docs/design/domain/BC-identidad-modelo.md`.
