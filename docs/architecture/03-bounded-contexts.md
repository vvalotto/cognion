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
invitación (RF-01), distinción de tres roles fijos — administrador, docente, estudiante (RF-02),
emisión y validación de JWT.

**Lenguaje ubicuo:** Usuario, Rol, Credencial, Token, Invitación.

**Frontera:** es el único BC que emite y valida identidad/rol. Ningún otro BC implementa su
propia autenticación — consumen la validación de Identidad a través de un puerto (ver
`20-context-map-integrations.md`).

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

**Frontera:** no tiene estado propio de escritura ni lógica de negocio — es enteramente derivado
del event store de Actividad Evaluativa. No modifica el estado de ningún otro BC.

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

Ningún BC importa código de otro directamente. Toda comunicación cruza por puertos definidos en
`entities/ports/` de cada BC, salvo las excepciones ya documentadas por ADR (Actividad
Evaluativa → Notificaciones, `ADR-006`; Analytics leyendo el event store compartido de Actividad
Evaluativa, `ADR-002`). `shared/entities/` es la excepción transversal para tipos y utilidades
sin lógica de negocio de un BC específico (`CLAUDE.md`); `shared/frameworks/` (desde `US-1.1.0`,
`ADR-017`) es la excepción análoga para infraestructura técnica pura — engine y sesión async de
SQLAlchemy compartidos por todos los BC contra la misma instancia de PostgreSQL (`ADR-004`,
`ADR-018` para el uso de `NullPool`). JWT/RBAC (verificación de token, roles) vive también en
`shared/` desde `ADR-019` (`shared/entities/`, `shared/frameworks/security/`,
`shared/interface_adapters/security/`) — cada BC sigue armando su propio composition root, sin
importar directamente de otro BC.

## Siguiente paso

El modelo de dominio detallado de Identidad (agregados, invariantes, eventos) se desarrolla en
`docs/design/domain/BC-identidad-modelo.md`, dentro de la Iteración 0 — Modelado del
Incremento 1. Los demás BC se detallan en su propia Iteración 0, uno por incremento — ver
`docs/rf/PLAN_v1.md`.
