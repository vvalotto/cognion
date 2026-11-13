# BL-017 — Incremento 10.1: Documentación de arquitectura y diseño detallado

| Campo | Valor |
|-------|-------|
| Tipo | Incremento documental (sin cambios en `src/`, `frontend/` ni `migrations/`; sin US-IEDD) |
| Fecha apertura | 2026-11-12 |
| Fecha cierre | 2026-11-13 |
| Git tag inicial | `v1.0.0` (`BL-016`) |
| Git tag cierre | **Ninguno.** No cambia el producto: no hay versión nueva ni imagen. `v1.0.0` sigue siendo la versión publicada |
| Milestone | Ninguno (decisión de Víctor: incremento documental sin US ni issues) |
| Estado | ✅ Completado, con los límites de *No verificado* |
| DoD | Vistas de arquitectura y de diseño detallado corregidas o creadas, contrastadas con el código de la `1.0.0`, con su método de verificación y lo no verificado declarado |

## Descripción

Corrige y completa la documentación técnica de arquitectura y de diseño detallado bajo un marco de vistas: C4 (contexto, contenedores, componentes) más datos, runtime, transversal, desarrollo y despliegue. Plan y relevamiento: `docs/plans/inc10-1/inc10-1-relevamiento-y-plan.md`. Un branch y un PR por fase.

| Fase | PR | Entregable |
|---|---|---|
| Previo | #630, #631 | Job `Alcance del cambio` en el CI (los PR de solo docs saltean los checks pesados) e indexado de `docs/INSTALACION.md` |
| 0 | #632 | Relevamiento de brechas, plan y plantilla de vista |
| 1 | #633 | `01-system-context` y `02-container-view` |
| 2 | #634, #635 | `10` a `14-componentes-*`, `03-bounded-contexts` y `20-context-map-integrations` |
| 3 | #636, #637 | `30-runtime-interactions`, `24` y `24a`; auditoría de `docs/design/domain/` |
| 4 | #638, #639 | `40-cross-cutting-concerns`, `50-development-view`, `60-deployment-view` y notas de vigencia en `ADR-021`, `022` y `024` |
| 5 | (este PR) | `70-trazabilidad-rnf-vistas`, `README` de `architecture/`, índices, matriz y `BL-017` |

## Inventario de Configuration Items

| CI | Artefacto | Tipo | Descripción |
|----|-----------|------|-------------|
| CI-D72 | `docs/architecture/` (vistas nuevas o reescritas: `01`, `02`, `03`, `10` a `14`, `20`, `24`, `24a`, `30`, `40`, `50`, `60`, `70`, más `_plantilla-vista.md` y `README.md`) | Documento | Descripción arquitectónica vigente de la `1.0.0` |
| CI-D73 | `docs/plans/inc10-1/` (`inc10-1-relevamiento-y-plan.md`, `auditoria-dominio.md`) | Documento | Plan, brechas y auditoría del dominio |
| CI-D74 | Notas de vigencia en `docs/design/domain/BC-*-modelo.md` (5) y los `ADR-021`, `022` y `024` | Documento | Diferencias con el código registradas sin reescribir el original |
| CI-T23 | `scripts/ci/alcance_cambio.sh`, job `alcance` de `.github/workflows/ci.yml`, `tests/unit/inc10/test_ci_alcance_cambio.py` | Tooling | Salteo de los checks pesados en PR de solo documentación |

## Métricas al cerrar

No hay cambios en el código del producto, por lo que **no se repitieron** la suite, la cobertura, `mypy`, `pylint`, `DesignReviewer` ni `ArchitectAnalyst`: valen las de `BL-016` (2459 tests, cobertura 97,03 %, 0 CRITICAL). El único código nuevo es el del CI: 18 tests nuevos del filtro de alcance y de la estructura del workflow (`tests/unit/inc10/test_ci_alcance_cambio.py`), que corrieron completos en el PR #630.

**Verificación de las vistas:** cada ruta de archivo citada en las vistas nuevas se comprobó con `os.path.exists`; los nombres de eventos, puertos e invariantes de los modelos de dominio se contrastaron con `src/` y `tests/` (`docs/plans/inc10-1/auditoria-dominio.md`); las rutas y los roles de cada router se extrajeron del código.

## Hallazgos del incremento

**Documentación corregida:** contenedores (la API sirve el frontend, Caddy según variante), catálogo de BC y mapa de contexto (`ADR-026`, `ADR-027`, puertos del Incremento 9), datos de Identidad (invitación grupal y bloqueo temporal), la firma de `CanalEnvioPort` en el modelo de Notificaciones, y el estado de los `ADR-021`, `022` y `024`.

**Distancias entre el `RNF_v1.md` y la `1.0.0`** (`70-trazabilidad-rnf-vistas.md`):
- **No cumple como está escrito:** el despliegue automático al hacer push a `main` (el CD construye y publica, no despliega) y el backup mensual con retención de 12 meses (hay un respaldo local con rotación de 30, sin automatización).
- **Parcial:** caída durante una sesión en vivo, dispositivos y navegadores, legibilidad de la proyección y observabilidad (el evento `SesionIniciada` se descarta y las conexiones no se registran).
- **No verificado:** mantenibilidad (un tipo de pregunta nuevo en ≤ 1 día).

**Otros:**
- `CLAUDE.md` dice Python 3.11 y el proyecto usa 3.12.
- Un comentario de `pyproject.toml` sobre el contrato de `ADR-026` quedó desactualizado.
- La variante del servidor Linux con Docker no tiene ADR propio.

## UAT de cierre
No aplica: no hay cambios funcionales. La evidencia de las vistas es la verificación contra el código descripta arriba.

**No verificado:**
- Las secuencias de `30-runtime-interactions.md` se contrastaron con los casos de uso y los features, pero **no se ejecutaron**.
- `portal-entrada-modelo.md` y los 8 HTML de `docs/design/domain/` no se auditaron.
- Que cada invariante del dominio se cumpla tal como el texto la describe.
- Las variantes de instalación con Docker siguen sin probarse contra Docker real (#624).

## Actualización de la matriz de trazabilidad
Sin cambios de estado de ningún RF ni RNF. La cabecera de `docs/traceability/matrix.md` registra el cierre. El estado de cada escenario de calidad se documenta en `docs/architecture/70-trazabilidad-rnf-vistas.md`, no en la matriz.

## Pendiente que queda abierto
- Decidir si se redactan: un ADR para la variante del servidor Linux con Docker y una revisión de `ADR-021`/`024`/`022`.
- Decidir qué hacer con los dos escenarios que no se cumplen (despliegue automático y backup mensual), que dependen de la decisión de infraestructura.
- Corregir `CLAUDE.md` (Python 3.12) y el comentario de `pyproject.toml` (cambios fuera de este incremento).
- [#624](https://github.com/vvalotto/cognion/issues/624): ensayo con Docker real; Incremento 11 (#616 a #619).

## Retrospectiva
- **Lo que funcionó:** el job de alcance volvió el costo de cada PR de documentación de ~25 minutos a minutos, lo que hizo viable un PR por fase; contrastar cada vista con el código (rutas, roles, adaptadores) encontró errores propios y ajenos antes de publicarlos; poner "Sin verificar" en cada vista evitó afirmar de más.
- **Lo que costó:** varias afirmaciones mías salieron mal al primer intento y se corrigieron al verificar (el rol de `mi-desempeno`, el bloqueo de cuenta, `docs/design/domain/` contra el código, una medición de rendimiento que sí existía). Conviene verificar cada afirmación puntual antes de escribirla y no al revisar.
- **Decisión de proceso:** se cerró sin tag ni versión porque el producto no cambia; el cierre documental queda en `develop`.
