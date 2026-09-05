# Incremento 4 — Portal del estudiante y Analytics — US candidatas

> Estado documental: **Iteración 0 — Modelado cerrada (2026-09-04).** `US-4.0.1` (modelo de
> dominio, Issue [#227](https://github.com/vvalotto/cognion/issues/227)) y `US-4.0.2`
> (wireframes, Issue [#228](https://github.com/vvalotto/cognion/issues/228)) aprobadas por
> Víctor. Milestone [`Incremento 4 — Portal del Estudiante y Analytics`](https://github.com/vvalotto/cognion/milestone/6)
> (corregido 2026-09-05 — el link apuntaba al Milestone #11, un duplicado vacío sin Issues;
> todos los Issues reales de este incremento usan el Milestone #6).
> Esta tabla ya puede usarse como base para elaborar las US-IEDD formales de las Iteraciones 1 y
> 2 (`WORKFLOW-DESARROLLO.md` §3, paso 1) — revisarla contra el modelo y los wireframes
> aprobados antes de crear Issues/specs, por si algo se ajustó respecto de lo anticipado acá —
> mismo criterio que `inc2-candidatas.md`/`inc3-candidatas.md`.
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

~~US-4.0.1~~ Cerrada 2026-09-04, Issue #227. ~~US-4.0.2~~ Cerrada 2026-09-04, Issue #228.

---

## Iteración 1 — RF-15: Estudiante ve su desempeño

A diferencia de Actividad Evaluativa, acá **no se difiere el frontend a una iteración
separada** — cada iteración cierra su propio RF de punta a punta (backend + frontend), mismo
criterio que Banco de Preguntas: el hito de esta iteración no cruza queries de otras
iteraciones (a diferencia de Actividad Evaluativa, donde el hito de cierre sí cruzaba 3
iteraciones de backend a la vez).

### Backend

| US | Descripción | Query | Actor | Precondición → Postcondición |
|---|---|---|---|---|
| **US-4.1.1** *(técnica)* | Infraestructura del BC Analytics: `EvaluacionDesempenoConsultaPort` con un único método `listar_evaluaciones_finalizadas(estudiante_id, materia_id?)` (`BC-analytics-modelo.md` §5), adapter in-process que lee la tabla `events` de Actividad Evaluativa (streams `Evaluacion`), composition root `src/analytics/frameworks/dependencies.py`, router base `analytics_router.py` | — (sin query de negocio propia) | — | Ninguna (primer código del BC) → mecanismo de lectura del event store ajeno probado, listo para que US-4.1.2 lo use |
| **US-4.1.2** | Estudiante consulta su propio desempeño en una materia — detalle por evaluación finalizada y resumen acumulado, ambos calculados a partir de la misma lectura (`BC-analytics-modelo.md` §6, hot spot 3: no hace falta una fuente separada para el acumulado) | `ObtenerDesempenoEstudianteUseCase` — compone `listar_evaluaciones_finalizadas(estudiante_id, materia_id)` y agrega en memoria | Estudiante (su propio `estudiante_id`, del token) | `Evaluacion` finalizadas del estudiante en la materia (puede ser ninguna) → lista de resultados por evaluación + resumen acumulado (correctas, incorrectas, % acierto, cantidad) |

**Endpoint propuesto:** `GET /analytics/materias/{materia_id}/mi-desempeno` (rol `estudiante`) —
a confirmar el path exacto en la spec de `US-4.1.2`.

### Frontend

| US | Descripción | Pantalla (`wireframes-analytics.md`) | Backend consumido | Depende de |
|---|---|---|---|---|
| **US-4.1.3** | Estudiante ve "Mi desempeño": selector de materia (reusa `GET /materias` del estudiante, `ListarMateriasDelEstudianteUseCase` ya existente — sin endpoint nuevo), resumen acumulado y detalle por evaluación | §2.0 `#est-desempeno` | `GET /analytics/materias/{materia_id}/mi-desempeno` (US-4.1.2) | US-4.1.2 |

**Orden de implementación:** US-4.1.1 primero (bloquea el resto del BC) → US-4.1.2 → US-4.1.3.

US-4.1.1 → Issue [#232](https://github.com/vvalotto/cognion/issues/232). US-4.1.2 → Issue
[#233](https://github.com/vvalotto/cognion/issues/233). US-4.1.3 → Issue
[#234](https://github.com/vvalotto/cognion/issues/234). Specs en `docs/specs/inc4/US-4.1.1.md`
a `US-4.1.3.md`.

---

## Iteración 2 — RF-16, RF-17: Desempeño por alumno y por tema (docente)

### Backend

| US | Descripción | Query | Actor | Precondición → Postcondición |
|---|---|---|---|---|
| **US-4.2.1** | Docente consulta el desempeño de un estudiante elegido — mismo detalle que ve el propio estudiante (RF-16) | Reutiliza `ObtenerDesempenoEstudianteUseCase` (US-4.1.2) sin cambios, invocado con el `estudiante_id` que el docente elige en vez del propio | Docente | `estudiante_id` existe (vía `EstudianteConsultaPort` o equivalente) → mismo resultado que US-4.1.2, para el estudiante elegido |
| **US-4.2.2** *(técnica)* | `ComisionConsultaPort` (`BC-analytics-modelo.md` §5) — puerto **nuevo de punta a punta**: requiere agregar en BC Identidad la query que hoy no existe (examinado en el modelado — `ComisionRepositoryPort`/`UsuarioRepositoryPort` solo resuelven por `id`). Agrega `listar_comisiones_por_materia(materia_id)` y `listar_estudiantes(comision_id)` del lado de Identidad, expuestas como endpoints HTTP propios (para poblar los selectores del frontend, US-4.2.5) y como adapter in-process para Analytics | — (sin query de negocio propia en Analytics; nueva capacidad de consulta en Identidad) | — | Ninguna query de "comisiones de una materia" ni "estudiantes de una comisión" hoy → ambas disponibles, consumidas por Identidad (HTTP) y Analytics (in-process) |
| **US-4.2.3** *(técnica)* | `PreguntaMetadatoConsultaPort` (`BC-analytics-modelo.md` §5) — adapter in-process hacia Banco de Preguntas, reusa `unidad_tematica`/`tema` ya expuestos por `MetadatosPregunta` (`US-ADJ-17`); sin endpoint HTTP propio, consumo interno de Analytics únicamente | — | — | Ninguna (dato ya existe en Banco de Preguntas) → `obtener_metadatos(pregunta_ids)` disponible para US-4.2.4 |
| **US-4.2.4** | Docente consulta la tasa de error por unidad/tema de una materia, agregada a toda la materia o acotada a una comisión (RF-17) | `ObtenerTasaErrorPorTemaUseCase` — compone `listar_respuestas_vigentes_de_materia(materia_id, estudiante_ids?)` (extensión de `EvaluacionDesempenoConsultaPort`, segundo método del puerto, no implementado todavía en Iteración 1), `ComisionConsultaPort.listar_estudiantes` (si `comision_id` viene informado) y `PreguntaMetadatoConsultaPort.obtener_metadatos` | Docente | Materia con `Evaluacion` finalizadas (puede no haber ninguna) → lista de `(unidad_tematica, tema)` con cantidad de respuestas, incorrectas y tasa de error, ordenada descendente |

**Endpoints propuestos:**
`GET /analytics/materias/{materia_id}/estudiantes/{estudiante_id}/desempeno` (US-4.2.1, rol
`docente`), `GET /materias/{materia_id}/comisiones` y `GET /comisiones/{comision_id}/estudiantes`
(US-4.2.2, BC Identidad), `GET /analytics/materias/{materia_id}/tasa-error-por-tema?comision_id=`
(US-4.2.4, rol `docente`) — a confirmar el path exacto en cada spec.

**Hot spot de autorización — resuelto con Víctor (2026-09-04):** cualquier docente autenticado
puede consultar el desempeño de cualquier estudiante — sin restringir a las comisiones que
dicta. `US-4.2.1` solo exige rol `docente` (RBAC estándar, sin invariante adicional de
pertenencia a comisión).

### Frontend

| US | Descripción | Pantalla (`wireframes-analytics.md`) | Backend consumido | Depende de |
|---|---|---|---|---|
| **US-4.2.5** | Docente ve "Desempeño por alumno": selectores en cascada materia → comisión → estudiante, reutiliza el componente visual de "Mi desempeño" (US-4.1.3) | §3.0 `#doc-desempeno-alumno` | `GET /materias/{materia_id}/comisiones`, `GET /comisiones/{comision_id}/estudiantes` (US-4.2.2), `GET /analytics/.../desempeno` (US-4.2.1) | US-4.2.1, US-4.2.2 |
| **US-4.2.6** | Docente ve "Desempeño por tema": selector materia/comisión, listado de tasa de error por tema con barra coloreada | §3.1 `#doc-desempeno-tema` | `GET /materias/{materia_id}/comisiones` (US-4.2.2), `GET /analytics/.../tasa-error-por-tema` (US-4.2.4) | US-4.2.4 |

**Orden de implementación:** US-4.2.2 y US-4.2.3 primero (infraestructura de puertos, sin
dependencia entre sí — pueden ir en paralelo). US-4.2.1 no depende de ninguna de las dos (reusa
el Use Case de Iteración 1) — puede implementarse en cualquier momento. US-4.2.4 depende de
US-4.2.2 y US-4.2.3 juntas. US-4.2.5 depende de US-4.2.1 y US-4.2.2; US-4.2.6 depende de
US-4.2.4 — ambas pantallas pueden avanzar en paralelo una vez resuelto su backend.

---

## DoD del Incremento (hito, `PLAN_v1.md`)

> Docente y estudiante tienen visibilidad de desempeño histórico basado en sesiones reales ya
> corridas en el incremento anterior.

---

## Próximos pasos

1. ~~Revisar esta propuesta de Iteración 0 con Víctor.~~ Hecho, alcance aprobado 2026-09-04.
2. ~~Crear Milestone GitHub `Incremento 4 — Portal del estudiante y Analytics` + Issues para
   US-4.0.1 y US-4.0.2.~~ Hecho — Milestone #6, Issues #227 (US-4.0.1) y #228 (US-4.0.2)
   (número de Milestone corregido 2026-09-05 — ver nota al inicio del documento).
3. ~~Ejecutar el diseño de read models (US-4.0.1) y los wireframes (US-4.0.2), con aprobación
   explícita de Víctor en cada Issue.~~ Hecho.
4. ~~Completar este archivo con el detalle de las Iteraciones 1 y 2.~~ Hecho — 2026-09-04.
5. ~~Revisar esta tabla de candidatas con Víctor.~~ Hecho — hot spot de autorización de
   `US-4.2.1` resuelto 2026-09-04 (cualquier docente consulta a cualquier estudiante). El
   agrupamiento de la infraestructura de puertos en `US-4.1.1`/`US-4.2.2`/`US-4.2.3` y los
   paths de endpoint quedan a confirmar en cada spec, no bloquean el arranque de la Iteración 1.
6. ~~Crear Issues (Milestone #6) y `docs/specs/inc4/US-4.M.K.md` de la Iteración 1.~~ Hecho
   2026-09-04 — Issues #232 (US-4.1.1), #233 (US-4.1.2), #234 (US-4.1.3).
7. ~~Implementar Iteración 1 (`/implement-us US-4.1.1` → `US-4.1.2` → `US-4.1.3`).~~ Hecho —
   cerrada 2026-09-05 (UAT aprobada con observaciones, `quality/reports/uat/inc4/`, PR #239 con
   los 2 fixes detectados en la UAT).
8. ~~Crear Issues (Milestone #6) y `docs/specs/inc4/US-4.2.K.md` de la Iteración 2.~~ Hecho
   2026-09-05 — Issues #240 (US-4.2.1), #241 (US-4.2.2), #242 (US-4.2.3), #243 (US-4.2.4),
   #244 (US-4.2.5), #245 (US-4.2.6).
9. Implementar Iteración 2. Orden: `US-4.2.2` y `US-4.2.3` primero (sin dependencia entre sí,
   desbloquean `US-4.2.4`); `US-4.2.1` en cualquier momento; `US-4.2.4` tras `US-4.2.2`/
   `US-4.2.3`; `US-4.2.5` tras `US-4.2.1`/`US-4.2.2`; `US-4.2.6` tras `US-4.2.4`.
