# Incremento 5 — Notificaciones — US candidatas

> Estado documental: **Iteración 0 — Modelado, borrador completo pendiente de aprobación
> explícita.** `US-5.0.1` (modelo de dominio, Issue
> [#304](https://github.com/vvalotto/cognion/issues/304),
> `docs/design/domain/BC-notificaciones-modelo.md`) — hot spots de producto ya resueltos con
> Víctor (2026-09-10, ver §6 del modelo), falta el comentario de aprobación en el Issue.
> Milestone [`Incremento 5 — Notificaciones`](https://github.com/vvalotto/cognion/milestone/7).
>
> Fuente: `docs/rf/PLAN_v1.md` §Incremento 5, `docs/rf/RF_v1.md` (RF-14), `docs/rf/ARQ_v1.md`
> (Notificaciones = Generic Subdomain, Event-driven), `ADR-006` (integración directa Actividad
> Evaluativa → Notificaciones, decisión ya cerrada — no se reabre en este modelado),
> `docs/design/domain/BC-actividad-evaluativa-modelo.md` (eventos `ActividadEvaluativaCreada`/
> `ActividadEvaluativaCerrada` existentes que este BC consume).

---

## Nota de contexto — qué cambia respecto de los BCs anteriores

Primer BC **event-driven puro** del sistema: no expone su propio comando desde un actor humano
(a diferencia de Identidad/Banco de Preguntas/Actividad Evaluativa) ni es de solo lectura (a
diferencia de Analytics) — reacciona a eventos de dominio ya existentes de otro BC y produce un
efecto de borde (enviar un email), sin aggregate propio con invariantes de negocio complejas.

Incremento corto y deliberadamente aislado (`PLAN_v1.md`): valida la integración BC Actividad
Evaluativa → BC Notificaciones documentada en `ADR-006` con el menor acoplamiento posible antes
de seguir agregando funcionalidad (Incremento 6, mayor riesgo técnico).

Sin Iteración 0 de UX — RF-14 no tiene pantalla propia (el email es el único artefacto
visible).

---

## Iteración 0 — Modelado (liviano)

Una US-IEDD tipo `Modelado` (`WORKFLOW-DESARROLLO.md` §1, §2) — DoD = artefacto aprobado
explícitamente por Víctor en el comentario que cierra el Issue. No genera spec en
`docs/specs/` — el propio Issue es la spec completa.

| US | Tipo | Descripción | Postcondición (DoD) | Path del artefacto |
|---|---|---|---|---|
| **US-5.0.1** | Modelado | Contrato de eventos consumidos desde Actividad Evaluativa (`ActividadEvaluativaCreada`/`ActividadEvaluativaCerrada`), forma de la `Notificacion` (destinatarios, contenido), puerto de integración directa (`ADR-006`), mecanismo de envío de email para el entorno actual (datos de prueba/locales, `PLAN_v1.md` revisión 2026-08-24) | Víctor aprueba el modelo en el comentario de cierre del Issue [#304](https://github.com/vvalotto/cognion/issues/304) | `docs/design/domain/BC-notificaciones-modelo.md` |

**Hot spots de producto, resueltos con Víctor 2026-09-10 (detalle en §6 del modelo):**
1. Cierre que dispara el email: solo `ActividadEvaluativaCerrada` (cierre manual, `US-3.3.2`) — no el vencimiento natural de `fecha_cierre`.
2. Destinatarios: solo estudiantes de las Comisiones a las que la actividad está restringida (`comisiones_ids`, vacío = todas las de la Materia).
3. Canal de envío en este entorno: SMTP real de prueba (Mailtrap/Mailhog local).
4. Manejo de fallos de envío: no bloquea — loguea y continúa, mismo criterio de "deuda técnica consciente" de `ADR-006`.

Al cerrar la Iteración 0: actualizar `docs/traceability/matrix.md` — RF-14 pasa de
*Planificado* a *Especificado*.

---

## Iteración 1 — RF-14: email de apertura/cierre

Pendiente de definir en detalle una vez cerrada la Iteración 0 — depende de las decisiones de
los hot spots de arriba. Candidatas anticipadas (a confirmar contra el modelo aprobado):

| US | Descripción tentativa |
|---|---|
| US-5.1.1 | Infraestructura del BC Notificaciones (entidad `Notificacion`, adapter de envío de email según lo decidido en Iteración 0) |
| US-5.1.2 | Envío de notificación al abrir una Actividad Evaluativa de período abierto |
| US-5.1.3 | Envío de notificación al cerrar una Actividad Evaluativa de período abierto |

**Hito del incremento:** el ciclo de la actividad de período abierto queda completo, incluida
la comunicación automática al estudiante.
