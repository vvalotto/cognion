# Incremento 4 — Portal del estudiante y Analytics — US candidatas

> Estado documental: **Iteración 0 — Modelado, en curso.** Alcance revisado y aprobado por
> Víctor 2026-09-04. Milestone [`Incremento 4 — Portal del estudiante y Analytics`](https://github.com/vvalotto/cognion/milestone/11)
> creado, Issues [#227](https://github.com/vvalotto/cognion/issues/227) (US-4.0.1) y
> [#228](https://github.com/vvalotto/cognion/issues/228) (US-4.0.2) abiertos. El detalle de las
> Iteraciones 1 y 2 se completa recién al cerrar la Iteración 0, contra el modelo y los
> wireframes ya aprobados, no antes — mismo criterio que `inc2-candidatas.md`/`inc3-candidatas.md`.
>
> Fuente: `docs/rf/PLAN_v1.md` §Incremento 4, `docs/rf/RF_v1.md` (RF-15, RF-16, RF-17 — RF-18
> queda fuera, es Incremento 7), `docs/rf/ARQ_v1.md` (Analytics = Supporting Subdomain, Read
> Models proyectados desde el event store de Actividad Evaluativa, sin persistencia propia de
> escritura), `ADR-002` (Event Sourcing + CQRS, ya implementado en Incremento 3),
> `docs/design/domain/BC-actividad-evaluativa-modelo.md` (event store existente que Analytics
> consume — no se modifica, solo se lee).

---

## Nota de contexto — qué cambia respecto de los BCs anteriores

Primer BC **puramente de lectura** del sistema: Analytics no tiene su propio comando ni evento
de dominio — se proyecta sobre el event store de Actividad Evaluativa (`ActividadEvaluativaCreada`,
`EvaluacionIniciada`, `RespuestaRegistrada`, `EvaluacionSuspendida`/`Reanudada`,
`EvaluacionFinalizada`, `PeriodoDisponibilidadModificado`, `ActividadEvaluativaCerrada`, ya
existentes desde el Incremento 3). No hay aggregate ni invariante de escritura que modelar —
el trabajo de la Iteración 0 es de **diseño de read models** (qué proyecciones, sobre qué
eventos, con qué forma de consulta) más los wireframes de las pantallas que los consumen.

RF-15 (vista de estudiante) menciona también sesiones en vivo ("para sesiones en vivo, ve su
puntaje y posición en el ranking") — ese tipo de sesión no existe todavía (Incremento 6). El
alcance de este incremento se limita a evaluaciones de período abierto, único tipo de dato
disponible; la sección de RF-15 sobre sesiones en vivo se retoma cuando exista ese BC.

---

## Iteración 0 — Modelado (liviano)

Dos US-IEDD **tipo `Modelado`** (`WORKFLOW-DESARROLLO.md` §1, §2) — DoD = artefacto aprobado
explícitamente por Víctor en el comentario que cierra el Issue. Ambas deben estar cerradas
antes de pasar a la Iteración 1. Las US tipo `Modelado` no generan spec en `docs/specs/` — el
propio Issue es la spec completa.

| US | Tipo | Descripción | Postcondición (DoD) | Path del artefacto |
|---|---|---|---|---|
| **US-4.0.1** | Modelado | Diseño de read models de Analytics sobre el event store de Actividad Evaluativa: proyección de desempeño individual por estudiante (RF-15/16, correctas/incorrectas por evaluación y acumuladas), proyección agregada por comisión/tema (RF-17, tasa de error por unidad/tema), mecanismo de proyección (query directa vs. proyección materializada — mismo tipo de decisión que `US-3.2.4` resolvió para `evaluaciones_activas_por_actividad`, documentada como reversible), puertos de consulta necesarios (`AnalyticsQueryPort` o equivalente) | Víctor aprueba el modelo en el comentario de cierre del Issue | `docs/design/domain/BC-analytics-modelo.md` |
| **US-4.0.2** | Modelado | Wireframes del portal de desempeño: vista de estudiante (historial de evaluaciones propias, detalle correctas/incorrectas por pregunta — RF-15), vista de docente por alumno (selecciona un estudiante de una comisión, ve su historial completo — RF-16), vista de docente por curso/tema (desempeño agregado de la comisión, temas con mayor tasa de error — RF-17) | Víctor aprueba los wireframes/prototipo en el comentario de cierre del Issue | `docs/design/ux/wireframes-analytics.md` + prototipo en `docs/design/ux/prototipos/` |

**Orden:** sin dependencia estricta entre sí, pero conviene US-4.0.1 antes que US-4.0.2 — las
pantallas dependen de qué datos expone cada read model (mismo orden que Incremento 3).

Al cerrar la Iteración 0: actualizar `docs/traceability/matrix.md` §4 — los escenarios RF-15,
RF-16, RF-17 pasan de *Planificado* a *Especificado* (`WORKFLOW-DESARROLLO.md` §3, paso 0e).

US-4.0.1 → Issue #227 (abierto). US-4.0.2 → Issue #228 (abierto).

---

## Iteración 1 y 2 — a completar al cerrar la Iteración 0

Según `PLAN_v1.md`:
- **Iteración 1:** RF-15 — vista de desempeño individual del estudiante.
- **Iteración 2:** RF-16, RF-17 — seguimiento por alumno y por curso/tema (docente).

El desglose en US-IEDD concretas (comandos/queries, endpoints, pantallas) se completa recién
con el modelo y los wireframes aprobados en mano — mismo criterio que `inc2-candidatas.md`/
`inc3-candidatas.md`.

---

## DoD del Incremento (hito, `PLAN_v1.md`)

> Docente y estudiante tienen visibilidad de desempeño histórico basado en sesiones reales ya
> corridas en el incremento anterior.

---

## Próximos pasos

1. ~~Revisar esta propuesta de Iteración 0 con Víctor.~~ Hecho, alcance aprobado 2026-09-04.
2. ~~Crear Milestone GitHub `Incremento 4 — Portal del estudiante y Analytics` + Issues para
   US-4.0.1 y US-4.0.2.~~ Hecho — Milestone #11, Issues #227 (US-4.0.1) y #228 (US-4.0.2).
3. Ejecutar el diseño de read models (US-4.0.1) y los wireframes (US-4.0.2), con aprobación
   explícita de Víctor en cada Issue.
4. Completar este archivo con el detalle de las Iteraciones 1 y 2, mismo formato que
   `inc3-candidatas.md`.
5. Crear Issues y `docs/specs/inc4/US-4.M.K.md` por cada US aprobada.
6. Implementar Iteración 1 → 2.
