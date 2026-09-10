# Incremento 5 — Notificaciones — US candidatas

> Estado documental: **Iteración 0 — Modelado cerrada (2026-09-10).** `US-5.0.1` (modelo de
> dominio, Issue [#304](https://github.com/vvalotto/cognion/issues/304),
> `docs/design/domain/BC-notificaciones-modelo.md`) aprobada por Víctor. Milestone
> [`Incremento 5 — Notificaciones`](https://github.com/vvalotto/cognion/milestone/7).
> Esta tabla ya puede usarse como base para elaborar las US-IEDD formales de la Iteración 1
> (`WORKFLOW-DESARROLLO.md` §3, paso 1).
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

~~US-5.0.1~~ Cerrada 2026-09-10, Issue #304.

---

## Iteración 1 — RF-14: email de apertura/cierre

**Especificada 2026-09-10** — specs completas en `docs/specs/inc5/`, Issues creados en el
Milestone [Incremento 5](https://github.com/vvalotto/cognion/milestone/7).

| US | Descripción | Spec | Issue |
|---|---|---|---|
| US-5.1.1 | Infraestructura del BC Notificaciones — `CanalEnvioPort`/`SmtpCanalEnvio` (SMTP local de prueba), `ComisionConsultaPort` propio de Notificaciones (con `email`, adapter in-process hacia un método nuevo de Identidad), contrato de `NotificacionPort` sin cablear todavía | `docs/specs/inc5/US-5.1.1.md` | [#307](https://github.com/vvalotto/cognion/issues/307) |
| US-5.1.2 | Envío de notificación al crear una Actividad Evaluativa de período abierto — cablea `NotificacionPort` en `CrearActividadPeriodoAbiertoUseCase` | `docs/specs/inc5/US-5.1.2.md` | [#308](https://github.com/vvalotto/cognion/issues/308) |
| US-5.1.3 | Envío de notificación al cerrar manualmente una Actividad Evaluativa de período abierto — cablea `NotificacionPort` en `CerrarActividadUseCase`; el vencimiento natural del período no dispara email | `docs/specs/inc5/US-5.1.3.md` | [#309](https://github.com/vvalotto/cognion/issues/309) |

Orden de dependencia: `US-5.1.1` → `US-5.1.2` → `US-5.1.3` (secuencial, cada una construye
sobre la anterior — no hay paralelismo posible dentro de esta iteración).

**Hito del incremento:** el ciclo de la actividad de período abierto queda completo, incluida
la comunicación automática al estudiante. `US-5.1.3` cierra completa la Iteración 1 y el
Incremento 5.
