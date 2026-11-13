# 03 Bounded Contexts

## Propósito

Catalogar los Bounded Contexts (BC) de Cognión: su responsabilidad, tipo estratégico DDD y
lenguaje ubicuo. Es el punto de entrada para entender cómo se descompone el dominio antes de
profundizar en cada uno.

## Alcance

Incluye:

- el catálogo completo de los 5 BC identificados en `ARQ_v1.md`, con su responsabilidad y
  fronteras a alto nivel;
- la clasificación estratégica DDD (Core / Supporting / Generic) de cada uno;
- el lenguaje ubicuo propio de cada BC.

No incluye el modelo de dominio detallado por BC (agregados, invariantes, eventos — eso vive en
`docs/design/domain/`, uno por BC, a medida que se modela en su propia Iteración 0) ni el detalle
de cómo colaboran en runtime (eso vive en `20-context-map-integrations.md`).

## Fuentes

- `docs/rf/ARQ_v1.md` — tabla de BCs y lenguaje ubicuo (histórica, no se modifica).
- `docs/adr/ADR-001-monolito-modular-clean-architecture.md` — los BC son módulos de un mismo
  proceso, no servicios independientes.
- `docs/adr/ADR-015-renombrar-bc-sesiones-actividad-evaluativa.md` — el BC "Sesiones" de
  `ARQ_v1.md` se llama, desde el 2026-07-16, **Actividad Evaluativa**.

## Catálogo de Bounded Contexts

| BC | Tipo DDD | Estado de modelado | Incremento(s) |
|----|----------|---------------------|------------|
| **Identidad** | Generic | Implementado — RF-01, RF-02, RF-03, RF-19, RF-24, RF-25 `Validado`; amplía RF-01 (portal de entrada, gestión de Comisiones) y autoservicio de contraseña en incrementos posteriores | Incremento 1; ampliado en 3-ADJ, 4-ADJ, 5-ADJ, 6-ADJ |
| **Banco de Preguntas** | Supporting | Implementado — RF-04, RF-05, RF-06 `Validado`; RF-07 (import PDF) `Planificado` | Incremento 2; ampliado en 4-ADJ, 6-ADJ |
| **Actividad Evaluativa** | Core Domain | Implementado (antes "Sesiones", ver `ADR-015`) — RF-11/RF-11b/RF-12/RF-13 (período abierto) `Validado`; RF-08/RF-09/RF-10 (modo en vivo, agregado hermano `ActividadEvaluativaPeriodoAbierto`/`ActividadEvaluativaEnVivo`) `Implementado`, `Validado` recién al cierre de `BL-011` | Incremento 3 (período abierto); Incremento 6 + 6-ADJ (modo en vivo) |
| **Analytics** | Supporting | Implementado — RF-15 a RF-17 y RF-20 a RF-23 `Validado`; RF-18 `Planificado` | Incremento 4; ampliado en 5-ADJ, 6-ADJ |
| **Notificaciones** | Generic | Implementado — RF-14 `Validado`, primer BC puramente reactivo (sin aggregate ni persistencia propia) | Incremento 5 |

Estado de madurez por RF: ver `docs/traceability/matrix.md` (fuente de verdad de trazabilidad —
esta tabla resume el estado del BC como módulo, no reemplaza la matriz).

### Identidad

**Responsabilidad:** gestión de usuarios, roles y autenticación. Registro de estudiantes por
invitación individual o grupal con vencimiento y revocación (RF-01, `ADR-012`, `ADR-027`), distinción de tres roles fijos — administrador, docente, estudiante (RF-02), comisiones y asignación de docentes, bloqueo de cuenta y recuperación de contraseña, y emisión del JWT.

**Lenguaje ubicuo:** Usuario, Rol, Credencial, Token, Invitación.

**Frontera:** es el único BC que autentica y emite el JWT. La verificación del token y los roles (RBAC) viven en `shared/` (`ADR-019`) y cada router de los demás BC la aplica con sus dependencias; ningún otro BC implementa su propia autenticación. Los demás BC consultan a Identidad por datos (comisiones, usuarios) a través de puertos propios (ver `20-context-map-integrations.md`).

### Banco de Preguntas

**Responsabilidad:** carga, tipificación y metadatos de preguntas (RF-04, RF-05, RF-06).
Provee el catálogo de `PreguntaPlantilla` que el BC Actividad Evaluativa selecciona al armar
una actividad.

**Lenguaje ubicuo:** PreguntaPlantilla, TipoPregunta, UnidadTemática, Dificultad, Importancia.

**Frontera:** no conoce el ciclo de vida de una actividad evaluativa ni las respuestas de los
estudiantes — solo expone el catálogo de preguntas disponibles y sus metadatos de filtrado.

### Actividad Evaluativa

*(Antes "Sesiones" — renombrado el 2026-07-16 por ambigüedad del término, ver `ADR-015`.)*

**Responsabilidad:** Core Domain del sistema. Ciclo de vida de actividades evaluativas en vivo
y de período abierto, ranking, persistencia de respuestas respuesta a respuesta (RF-11 a RF-13,
RF-08 a RF-10). Modelado con Event Sourcing + CQRS (`ADR-002`).

**Lenguaje ubicuo:** ActividadEvaluativa, PreguntaAsignada, Respuesta, Ranking,
ActividadEvaluativaEnVivo, ActividadEvaluativaPeriodoAbierto.

**Frontera:** es el único BC con event store propio (tabla append-only `events`). Selecciona
preguntas del Banco de Preguntas y desencadena notificaciones, pero su propio ciclo de vida
(commands, eventos, invariantes) es interno y no se expone a otros BC salvo a través del event
store (consumido por Analytics) y de la integración directa con Notificaciones (`ADR-006`).

### Analytics

**Responsabilidad:** proyecciones de solo lectura sobre el event store de Actividad Evaluativa
— desempeño individual del estudiante (RF-15), seguimiento por alumno y por curso/tema (RF-16,
RF-17).

**Lenguaje ubicuo:** ReadModel, Proyección, MétricaDeActividadEvaluativa.

**Frontera:** no tiene estado propio de escritura ni lógica de negocio de escritura: es de solo lectura y se calcula al consultar. Lee el event store y los read models de Actividad Evaluativa y los metadatos de pregunta de Banco directamente por sus modelos ORM (excepción de `ADR-026`, solo en adaptadores de lectura), y a Identidad por sus gateways. No modifica el estado de ningún otro BC.

### Notificaciones

**Responsabilidad:** envío de comunicaciones — hoy, email de apertura/cierre de actividad
evaluativa de período abierto (RF-14); extensible a otros canales.

**Lenguaje ubicuo:** Notificación, Canal, Evento de integración.

**Frontera:** no conoce el dominio de Actividad Evaluativa más allá del evento puntual que
dispara cada notificación. Recibe la orden de notificar desde Actividad Evaluativa vía llamada
directa a su Use Case (`ADR-006`), no consume el event store completo.

**Nota:** BC Identidad ya tiene, desde el Incremento 1, su propio mecanismo de envío de email
para invitaciones (`ADR-012`), independiente del de este BC — deuda técnica consciente,
revisada en `US-5.1.1`: se mantienen dos adaptadores SMTP separados por BC, pero
`SmtpCanalEnvio` reutiliza la misma técnica (`smtplib` + `asyncio.to_thread`) que
`SmtpNotificador` de Identidad, sin sumar una dependencia async nueva.

## Regla de comunicación entre BCs

Ningún BC importa código de otro fuera de `frameworks/adapters/`. Toda comunicación cruza por puertos definidos en `entities/ports/` del BC consumidor, y su implementación es un adaptador en `frameworks/adapters/`. Las capas dentro de cada BC (`entities ← use_cases ← interface_adapters ← frameworks`) y este aislamiento **los hace cumplir `import-linter` en el CI** (`uv run lint-imports`, 4 contratos en `pyproject.toml`); el detalle está en `20-context-map-integrations.md`.

Excepciones documentadas:
- Actividad Evaluativa → Notificaciones por llamada directa a sus casos de uso (`ADR-006`).
- Analytics lee modelos ORM de otros BC (`ADR-026`): es el único BC con ese permiso. Desde el Incremento 9 (`BL-015`) ya no queda ninguna otra excepción puntual.
- Los repositorios SQL de `interface_adapters/gateways/` importan los modelos de `frameworks/db/models.py` de su propio BC (9 archivos de Identidad y Banco).

`shared/` es la excepción transversal para tipos y utilidades sin lógica de negocio de un BC: `shared/entities/` (tipos, JWT y RBAC, `ADR-019`), `shared/frameworks/` (engine y sesión async de SQLAlchemy, `ADR-017` y `ADR-018`; SMTP; logging; versión). Cada BC arma su propio composition root en `frameworks/dependencies.py`, importando de `shared`, nunca de otro BC.

## Siguiente paso

El detalle de cada BC por dentro está en `10` a `14-componentes-<bc>.md`; las relaciones entre ellos, en `20-context-map-integrations.md`; el modelo de dominio, en `docs/design/domain/`.
