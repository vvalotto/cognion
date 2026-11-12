# Incremento 10.1 — Documentación de arquitectura y diseño detallado

> Estado: **Fase 0 (relevamiento y marco)** — 2026-11-12. Incremento documental, **sin US-IEDD ni cambios en `src/`, `frontend/` ni `migrations/`**. Baseline prevista: `BL-017`.
> Decisiones de Víctor (2026-11-12): alcance = auditar y corregir lo existente **y** completar los huecos; marco = **C4** más vistas de despliegue, datos y runtime; público = quien instala, quien mantiene y la materia (todo); español, Markdown y Mermaid; sin US.

## 1. Objetivo y reglas

Que `docs/architecture/` y `docs/design/` describan **lo que el código hace hoy** (versión `1.0.0`), organizado en vistas que respondan las preguntas de cada interesado, y que se pueda mantener sin que se desfasen.

- **Descriptivo, no aspiracional.** Cada afirmación se contrasta con el código, los tests o un ADR; lo que no se pudo contrastar se marca `⚠ sin verificar`.
- **Autoridad:** código y tests > baselines > ADR > matriz > estas vistas > README (`CLAUDE.md`). Si una vista contradice al código, se corrige la vista.
- **No duplicar** lo que ya está en un ADR o en `docs/design/domain/`: se enlaza.
- **ADR y `ARQ_v1.md` no se reescriben retroactivamente.** Un ADR desactualizado se anota o se reemplaza con uno nuevo; no se edita su razonamiento original.
- **Un PR por fase**, solo `docs/` (+ `.cm/`, `quality/reports/` en el cierre): el CI pesado se saltea (`scripts/ci/alcance_cambio.sh`).

## 2. Marco de vistas

| Nivel / vista | Pregunta que responde | Quién la usa | Documento |
|---|---|---|---|
| C4-1 Contexto | ¿Qué es Cognión y con quién habla? | todos | `01-system-context.md` |
| C4-2 Contenedores | ¿Qué procesos y almacenes hay y con qué tecnología? | instalador, mantenedor | `02-container-view.md` |
| Catálogo de BC | ¿Cómo se parte el dominio? | mantenedor, materia | `03-bounded-contexts.md` |
| C4-3 Componentes (uno por BC) | ¿Cómo está armado cada BC por dentro (capas, casos de uso, puertos, adaptadores)? | mantenedor, materia | `10` a `14-componentes-<bc>.md` (nuevos) |
| Mapa de contexto | ¿Cómo se relacionan los BC y por qué puertos? | mantenedor, materia | `20-context-map-integrations.md` |
| Datos | ¿Qué tablas hay y quién las escribe? | mantenedor | `24`, `24a` a `24c` |
| Runtime (vista dinámica) | ¿Qué pasa de punta a punta en los casos críticos? | mantenedor, materia | `30-runtime-interactions.md` (nuevo) |
| Transversal | Seguridad, configuración, logging, errores, accesibilidad | mantenedor, instalador | `40-cross-cutting-concerns.md` (nuevo) |
| Desarrollo | Estructura del código, reglas de dependencias, CI/CD, versiones | mantenedor | `50-development-view.md` (nuevo) |
| Despliegue | ¿Dónde corre y cómo se instala/opera cada variante? | instalador | `60-deployment-view.md` (nuevo) |
| C4-4 / diseño detallado | Dominio por BC, secuencias, esquemas | mantenedor, materia | `docs/design/domain/` + `30-runtime-interactions.md` |

Cada vista usa `docs/architecture/_plantilla-vista.md` (propósito, interesados, alcance, fuentes, diagrama, elementos, relaciones, decisiones, restricciones, **cómo verificar contra el código**, **qué cambio obliga a actualizarla**).

## 3. Relevamiento: lo que hay y qué le falta

### 3.1 Vistas existentes contrastadas con el código (v1.0.0)

| Documento | Estado | Brechas verificadas |
|---|---|---|
| `01-system-context.md` | Correcto en lo esencial | Falta el actor operador/instalador y el canal de entrega de la versión (GitHub Release + imagen en GHCR). El texto dice "único docente"; el sistema ya modela varios docentes por comisión (`Comision`↔`Docente`). |
| `02-container-view.md` | **Desactualizada** | No describe cómo se sirve la SPA (`src/servidor.py`: API bajo `/api`, SPA en la raíz, mismo proceso) ni el proxy inverso (Caddy) de `deploy/servidor/` y `deploy/gcp/`. Dice que Notificaciones tiene tablas relacionales: no tiene persistencia propia. No nombra a Analytics en la persistencia. "Siguiente paso" obsoleto (promete documentos ya escritos). |
| `03-bounded-contexts.md` | **Desactualizada** | Dice que Analytics "es enteramente derivado del event store" y no menciona que `ADR-026` lo autoriza a leer también los modelos ORM de Identidad y Banco. La regla de comunicación no cita `import-linter` (cumplimiento automático en el CI) ni `ADR-026`. Sin invitación grupal (`ADR-027`). "Siguiente paso" obsoleto. |
| `20-context-map-integrations.md` | **Desactualizada** | No refleja los puertos nuevos del Incremento 9 (`NombreUsuarioQueryPort`, `EstudianteEvaluacionesQueryPort`, `ComisionQueryPort.existe_comision_en_materia`), ni la excepción de Analytics de `ADR-026`, ni `ADR-027`. La sección "Relaciones pendientes de definir" quedó resuelta hace tiempo. Última edición 2026-09-29. |
| `24-modelo-datos-postgresql.md`, `24a` a `24c` | Parcial | `24a` no incluye las columnas de la invitación grupal (migración `f7a3c9d15e82`). No dice que Notificaciones y Analytics **no** tienen tablas. Hay 14 tablas (13 modelos ORM más la asociativa `comision_docentes`) y 19 migraciones: sin tabla de verificación cruzada contra los modelos ORM. |
| `README.md` de `architecture/` | Desactualizado | Lista como "pendientes" `1X-bc-<nombre>`, `30`, `40` y `60`; propone cosas que se resolvieron de otra manera. |
| `docs/design/domain/` (6 modelos + 8 HTML) | **Sin auditar** | Estado "vigente", última actualización grande 2026-09-16. Pueden haber quedado atrás: invitación grupal, aviso del último intento, hash asíncrono, `Comision`/`Docente`, y los cambios del Incremento 9. Se audita en la Fase 3. |
| `docs/design/ux/` | Fuera de alcance | Es diseño de interfaz con su propio gate; no se toca. |

### 3.2 Vistas que no existen

| Vista | Qué falta | Fuente principal para escribirla |
|---|---|---|
| Componentes por BC (×5) | Casos de uso, puertos, adaptadores y routers de cada BC. Hoy hay solo modelo de dominio. | `src/<bc>/` (identidad: 28 casos de uso y 12 puertos; banco: 13 y 4; actividad evaluativa: 30 y 14; analytics: 7 y 5; notificaciones: 2 y 2) |
| Runtime | Secuencias de: registro por invitación grupal, login con bloqueo, período abierto, sesión en vivo (WebSocket, ranking), cierre de pregunta, recuperación de contraseña, envío de notificación | `use_cases/`, routers, `connection_manager.py`, tests BDD |
| Transversal | Seguridad (JWT, RBAC, bcrypt asíncrono, bloqueo), configuración y `ENTORNO`, logging JSON y enmascarado de tokens, `/health` y `/health/ready`, manejo de errores, accesibilidad | `ADR-007`, `013`, `014`, `019`; `src/settings.py`; `src/shared/frameworks/` |
| Desarrollo | Estructura del repo, contratos de `import-linter`, quality gates, CI/CD, versionado (`VERSION`, tag, Release, imagen) | `pyproject.toml`, `.github/workflows/`, `scripts/` |
| Despliegue | Variantes: local sin Docker, servidor Linux con Docker (db + app + Caddy), GCP; respaldo y restauración; migraciones; actualización y rollback | `deploy/`, `scripts/local/`, `docs/INSTALACION.md`, `ADR-022`, `024`, `025` |
| Trazabilidad de RNF | Qué vista y qué mecanismo cubren cada escenario de `RNF_v1.md` | `RNF_v1.md`, matriz |

### 3.3 Decisiones registradas que hay que reconciliar

- `ADR-021` ("Destino de despliegue de producción: Fly.io") y `ADR-024` (dominio y TLS) están **En revisión**; `ADR-021` conserva el título de Fly.io, que ya no se usa (`ADR-025`). `fly.toml` es histórico. Propuesta para la Fase 4: no editar el razonamiento; agregar una nota de vigencia y, si Víctor lo decide, un ADR nuevo para el despliegue en servidor Linux con Docker (`deploy/servidor/`), que hoy no tiene ADR propio.
- `ADR-012` (invitación por link) quedó reemplazado en la UI por `ADR-027` (grupal); el individual se conserva en el backend.

## 4. Fases

Cada fase: una rama `docs/inc-10-1-fase-N-<tema>`, un PR a `develop`, **Definición de hecho** propia. Se avanza con el visto bueno de Víctor al final de cada una.

| Fase | Entregable | Definición de hecho |
|---|---|---|
| **0 — Relevamiento y marco** (esta) | Este documento, plantilla de vista, índice objetivo en `README.md` de `architecture/` | Brechas listadas con evidencia; plan aprobado por Víctor |
| **1 — C4 niveles 1 y 2** | `01` y `02` corregidos; diagrama de contenedores con Caddy, SPA servida por la API, GHCR y el operador | Cada elemento y relación del diagrama apunta a un archivo del repo; sin texto en futuro obsoleto |
| **2 — C4 nivel 3 por BC** | `10` a `14-componentes-<bc>.md`; `03` y `20` actualizados (`ADR-026`, `ADR-027`, puertos del Incremento 9) | Los puertos y adaptadores listados coinciden con `src/` (verificado con un script o `ls`); lo que impone `import-linter` está citado |
| **3 — Diseño detallado** | `24a` corregido, `24` con la tabla de propiedad de tablas, `30-runtime-interactions.md` con las secuencias críticas, auditoría de `docs/design/domain/` con lista de diferencias corregidas | Cada secuencia se contrasta con un test BDD o de integración existente; diferencias del dominio resueltas o registradas |
| **4 — Vistas transversales** | `40-cross-cutting-concerns.md`, `50-development-view.md`, `60-deployment-view.md`; notas de vigencia en `ADR-021` y `024` | Cada variante de despliegue coincide con `docs/INSTALACION.md`; sin contradicciones con ADR vigentes |
| **5 — Cierre** | Trazabilidad de RNF a vistas, índices (`README.md`, `DOCUMENTATION-MAP.md`, `FUENTES-DE-VERDAD-DOCUMENTAL.md`), matriz, `BL-017`, retrospectiva, `/docs-audit` sin huérfanos | Verificación cruzada final contra el código; `BL-017` mergeada |

## 5. Cómo se verifica contra el código (método)

1. **Estructura:** `ls` de `src/<bc>/{use_cases,entities/ports,interface_adapters,frameworks}` y routers de `src/app.py`.
2. **Reglas de dependencias:** contratos de `[tool.importlinter]` en `pyproject.toml` y `tests/unit/inc9/test_guarda_arquitectura.py`.
3. **Datos:** modelos ORM (`src/*/frameworks/db/models.py`) y `migrations/versions/`.
4. **Runtime:** use cases, routers y features BDD (`tests/features/`).
5. **Despliegue:** `deploy/*/docker-compose.yml`, `Caddyfile`, `cognion.sh`, `scripts/local/`, `docs/INSTALACION.md`.
6. Todo lo que no se pueda contrastar queda marcado `⚠ sin verificar` en la vista y en la baseline.

## 6. Riesgos

- **Deriva:** una vista se desactualiza apenas cambia el código. Mitigación: cada vista declara qué cambio la invalida (plantilla) y el cierre de baseline incluye `/docs-audit`.
- **Volumen:** son unas 15 vistas nuevas o corregidas. Mitigación: fases cortas, con aprobación de Víctor entre una y otra.
- **Diagramas Mermaid grandes** ilegibles: un diagrama por pregunta, no uno por todo.
- **Material didáctico:** lo escrito para la materia necesita un nivel de explicación distinto al del mantenedor; se resuelve con una sección "Para leer esta vista" en cada una, no con documentos paralelos.

## 7. Qué queda fuera

Cambios de código, nuevas US, diseño de interfaz (`docs/design/ux/`), reescritura de `ARQ_v1.md` y ADR históricos, y la documentación de las mejoras del Incremento 11 (se documentan cuando se implementen).
