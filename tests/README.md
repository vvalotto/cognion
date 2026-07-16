# tests/

Cuatro niveles, cada uno particionado por incremento (`incN/`):

| Carpeta | Nivel | Qué valida |
|---|---|---|
| `unit/incN/` | Unitario | Entities y use_cases en aislamiento — sin infraestructura. |
| `integration/incN/` | Integración | Interface adapters + frameworks contra dependencias reales (DB, etc.). |
| `features/incN/` | BDD / funcional | Escenarios de comportamiento por US-IEDD. |
| `uat/incN/` | Aceptación de usuario | Ejecución manual/asistida — procedimiento completo en
`docs/plans/PROCEDIMIENTO-UAT.md`, no se repite acá. |

`incN` corresponde al número de Incremento definido en `docs/rf/PLAN_v1.md` — no a la
US individual. El mapeo de qué evidencia corresponde a qué US vive en
`docs/traceability/matrix.md`.
