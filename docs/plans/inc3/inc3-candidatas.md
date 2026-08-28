# Incremento 3 — Actividad Evaluativa, período abierto — US candidatas

> Estado documental: **Iteración 0 — Modelado cerrada (2026-08-25/26).** `US-3.0.1` (modelo de
> dominio, Issue #137) y `US-3.0.2` (wireframes, Issue #138) aprobadas por Víctor. Esta tabla ya
> puede usarse como base para elaborar las US-IEDD formales de las Iteraciones 1 a 4
> (WORKFLOW-DESARROLLO.md §3, paso 1) — revisarla contra el modelo y los wireframes aprobados
> antes de crear los Issues y specs, por si algo se ajustó respecto de lo anticipado acá (mismo
> criterio que `inc2-candidatas.md`).
>
> Fuente: `docs/rf/PLAN_v1.md` §Incremento 3 (revisión 2026-08-24 incluida — ver nota de
> estrategia de datos de prueba más abajo), `docs/rf/RF_v1.md` (RF-11, RF-11b, RF-12, RF-13),
> `docs/rf/RNF_v1.md` (Confiabilidad — escenario de interrupción durante sesión de período
> abierto), `ADR-002` (Event Sourcing + CQRS, Aceptado), `ADR-009` (Unit of Work por Use Case,
> Aceptado), `ADR-015` (BC renombrado de "Sesiones" a "Actividad Evaluativa", Aceptado — usar el
> nombre nuevo en todo artefacto nuevo: paths, código, Issues),
> `docs/design/domain/BC-actividad-evaluativa-modelo.md`,
> `docs/design/ux/wireframes-actividad-evaluativa.md`.

---

## Nota de contexto — estrategia de datos y gate de infraestructura

`PLAN_v1.md` (texto original) condicionaba el arranque de este incremento a resolver antes los
ítems abiertos de infraestructura de producción y backup, por ser el primer incremento con
"datos reales de estudiantes en juego". Revisión 2026-08-24 (decisión de Víctor, PR #135):
los Incrementos 3 a 7 corren con datos de prueba/locales, no datos reales de estudiantes en
producción — esa decisión institucional se resuelve recién en la última iteración antes de la
prueba funcional de validación previa al despliegue real. **El gate no bloquea el arranque de
este incremento.**

---

## Iteración 0 — Modelado

Dos US-IEDD **tipo `Modelado`** (WORKFLOW-DESARROLLO.md §1, §2) — DoD = artefacto aprobado
explícitamente por Víctor en el comentario que cierra el Issue. Ambas deben estar cerradas
antes de pasar a la Iteración 1.

Es el primer **Core Domain** del sistema (`ARQ_v1.md`, driver 3) y el primer BC con
**Event Sourcing + CQRS** (`ADR-002`) — a diferencia de Identidad y Banco de Preguntas, que
usan repositorios CRUD estándar. No existe todavía infraestructura de event store append-only
reutilizable de los BCs anteriores; el modelado debe cubrirla.

| US | Tipo | Descripción | Postcondición (DoD) | Path del artefacto |
|---|---|---|---|---|
| **US-3.0.1** | Modelado | Event storming BC Actividad Evaluativa: aggregate `ActividadEvaluativa` (período abierto), eventos de dominio (`SesionCreada`, `RespuestaRegistrada`, `SesionCerrada`, `PeriodoDisponibilidadModificado`), comandos, invariantes de persistencia atómica respuesta a respuesta (RNF Confiabilidad), invariante de set de preguntas fijo desde el inicio de la sesión, invariante de no acortar el período con estudiantes activos (RF-11b, caso límite), y el diseño concreto del event store append-only (mecanismo de persistencia, no solo el agregado) | Víctor aprueba el modelo en el comentario de cierre del Issue | `docs/design/domain/BC-actividad-evaluativa-modelo.md` |
| **US-3.0.2** | Modelado | Wireframes del flujo de período abierto: creación de sesión por el docente (materia, ventana de disponibilidad, cantidad de preguntas/intentos), extensión de plazo en caliente sobre una sesión activa, toma del examen por el estudiante (incluida la reconexión sin pérdida de respuestas), revisión al finalizar | Víctor aprueba los wireframes/prototipo en el comentario de cierre del Issue | `docs/design/ux/wireframes-actividad-evaluativa.md` + prototipo en `docs/design/ux/prototipos/` |

Al cerrar la Iteración 0: actualizar `docs/traceability/matrix.md` §4 — los escenarios RF-11,
RF-11b, RF-12, RF-13 y RNF-CONF-1/RNF-DISP-2 pasan de *Planificado* a *Especificado*
(WORKFLOW-DESARROLLO.md §3, paso 0e). **Hecho** — ver `docs/traceability/matrix.md` líneas
110-113, 239-240.

~~US-3.0.1~~ Cerrada 2026-08-25, Issue #137. ~~US-3.0.2~~ Cerrada 2026-08-26, Issue #138.

---

## Iteración 1 — RF-11, RF-12: creación de actividad y set aleatorio por estudiante

Primer BC con Event Sourcing + CQRS (`ADR-002`) — no hay infraestructura de event store
reutilizable de Identidad ni Banco de Preguntas (ambos CRUD estándar), así que la Iteración
arranca con una US técnica de infraestructura.

### Backend

| US | Descripción | Comando | Evento(s) | Actor | Invariantes clave | Precondición → Postcondición |
|---|---|---|---|---|---|---|
| **US-3.1.1** *(técnica)* | Infraestructura de Event Sourcing + CQRS del BC: tabla `events` (JSONB, PostgreSQL), append/replay por stream `(aggregate_type, aggregate_id)`, Unit of Work por Use Case (`ADR-009`), concurrencia optimista por `sequence_number` (`BC-actividad-evaluativa-modelo.md` §6) | — (sin comando de negocio propio) | — | — | Escritura y replay atómicos, sin invariante de dominio propia | Ninguna (primer código del BC) → mecanismo de append/replay probado con un aggregate de ejemplo, listo para que US-3.1.2/3.1.3 lo usen |
| **US-3.1.2** | Docente crea una actividad de período abierto (materia, ventana, cantidad de preguntas, intentos permitidos) | `CrearActividadPeriodoAbierto(materia_id, fecha_apertura, fecha_cierre, cantidad_preguntas, cantidad_intentos_permitidos)` | `ActividadEvaluativaCreada` | Docente | INV-AE-01 (preguntas suficientes en el banco), INV-AE-02 (apertura < cierre), INV-AE-03 (intentos ≥ 1) | `Materia` con `Banco` existente (vía `MateriaConsultaPort`/`PreguntaConsultaPort`), docente autenticado → `ActividadEvaluativaPeriodoAbierto` persistida como primer evento de su stream |
| **US-3.1.3** | Estudiante inicia su evaluación — se le fija un set aleatorio de preguntas (RF-12), reconectarse retoma sin generar uno nuevo | `IniciarEvaluacion(actividad_id, estudiante_id)` | `EvaluacionIniciada` | Estudiante | INV-AE-05 (set fijo desde el inicio), INV-AE-06 (a lo sumo una `Evaluacion` en curso por par, idempotente), `FueraDePeriodo` si no está dentro de la ventana vigente | `ActividadEvaluativaPeriodoAbierto` vigente, estudiante existe (vía `EstudianteConsultaPort`) → `Evaluacion` creada con `preguntas_asignadas` sampleadas al azar (o retomada si ya existía una en curso) |

**Orden de implementación:** US-3.1.1 primero (bloquea todo el resto del BC). US-3.1.2 antes
que US-3.1.3 (no se puede iniciar una evaluación de una actividad que no existe).

~~US-3.1.1~~ Issue #145. ~~US-3.1.2~~ Issue #146. ~~US-3.1.3~~ Issue #147. Specs en
`docs/specs/inc3/US-3.1.1.md`, `US-3.1.2.md`, `US-3.1.3.md`.

---

## Iteración 2 — RNF Confiabilidad, RF-13: persistencia respuesta a respuesta, revisión al finalizar

### Backend

| US | Descripción | Comando/Query | Evento(s) | Actor | Invariantes clave | Precondición → Postcondición |
|---|---|---|---|---|---|---|
| **US-3.2.1** | Estudiante confirma una respuesta — persistencia atómica, respuesta a respuesta (RNF Confiabilidad) | `RegistrarRespuesta(evaluacion_id, pregunta_id, respuesta)` | `RespuestaRegistrada` | Estudiante | INV-AE-07 (pregunta asignada, `Evaluacion` `EnCurso`, dentro de período), INV-AE-08 (intentos no agotados), INV-AE-09 (transacción propia por respuesta, `ADR-009`), INV-AE-10 (corrección calculada e inmutable al momento de crear la `Respuesta`) | `Evaluacion` `EnCurso`, pregunta pertenece al set asignado → nueva `Respuesta` (Entity, `id` propio) persistida en su propia transacción |
| **US-3.2.2** | Estudiante pausa su evaluación (manual) y la reanuda explícitamente | `SuspenderEvaluacion(evaluacion_id)` / `ReanudarEvaluacion(evaluacion_id)` | `EvaluacionSuspendida` / `EvaluacionReanudada` | Estudiante | INV-AE-11 (solo se reanuda una `Suspendida`), INV-AE-12 (`RegistrarRespuesta` exige `EnCurso`, rechaza sobre `Suspendida`) | `Evaluacion` `EnCurso` → `Suspendida` (o inversa, retoma en el mismo punto, mismo set y respuestas) |
| **US-3.2.3** | Estudiante finaliza su evaluación (explícito) y ve la revisión completa | `FinalizarEvaluacion(evaluacion_id)`; `ObtenerRevisionEvaluacion(evaluacion_id)` (query) | `EvaluacionFinalizada` | Estudiante | — | `Evaluacion` `EnCurso`/`Suspendida` → `Finalizada`; detalle por pregunta disponible de inmediato (RF-13: respuesta propia, correcta/incorrecta, respuesta correcta si falló) — nunca antes de finalizar |
| **US-3.2.4** *(técnica)* | `VerificadorDeVencimientos` — Policy periódica que dispara automáticamente lo que un actor humano no disparó a tiempo: Regla 1 (inactividad → `SuspenderEvaluacion`) y Regla 2 (vencimiento pasivo del período → `FinalizarEvaluacion`), ambas idempotentes (`BC-actividad-evaluativa-modelo.md` §6b) | reutiliza los comandos de US-3.2.2/US-3.2.3, actor = Sistema | mismos eventos que US-3.2.2/US-3.2.3 | Sistema (job periódico o chequeo perezoso, cadencia a definir en la spec) | Reglas 1/2 son no-op sobre una `Evaluacion` que ya cambió de estado por otra vía (protegido por INV-AE-11/12) | Read model `evaluaciones_activas_por_actividad` con `Evaluacion` inactiva/vencida → comando emitido con actor `sistema`, sin intervención humana |

**Orden de implementación:** US-3.2.1 primero (habilita el resto — sin respuestas no hay nada
que suspender/finalizar/revisar). US-3.2.2 antes que US-3.2.3 (finalizar desde `Suspendida`
requiere que la suspensión ya exista). US-3.2.4 al final — reutiliza los Use Case de
US-3.2.2/US-3.2.3 tal cual, solo cambia quién los invoca; también es donde se construye el read
model `evaluaciones_activas_por_actividad` que reutilizará US-3.3.1.

---

## Iteración 3 — RF-11b: modificación del período de disponibilidad en caliente

### Backend

| US | Descripción | Comando | Evento(s) | Actor | Invariantes clave | Precondición → Postcondición |
|---|---|---|---|---|---|---|
| **US-3.3.1** | Docente extiende (o intenta acortar) el plazo de una actividad vigente | `ModificarPeriodoDisponibilidad(actividad_id, nueva_fecha_cierre)` | `PeriodoDisponibilidadModificado` | Docente | INV-AE-02 (apertura < nuevo cierre), INV-AE-04 (rechaza acortar si hay `Evaluacion` activa — `EnCurso` o `Suspendida`, vía read model `evaluaciones_activas_por_actividad`), INV-AE-04b (rechaza si `cerrada_manualmente`) | `ActividadEvaluativaPeriodoAbierto` no cerrada manualmente → `fecha_cierre` actualizada (extender siempre permitido; acortar solo sin evaluaciones activas) |
| **US-3.3.2** | Docente cierra una actividad manualmente antes de tiempo (medida opcional, no un paso obligatorio del ciclo de vida) | `CerrarActividad(actividad_id)` | `ActividadEvaluativaCerrada` (+ `FinalizarEvaluacion` en cascada sobre cada `Evaluacion` activa, Regla 3 de la Policy, síncrona) | Docente | INV-AE-04b (terminal, no admite `ModificarPeriodoDisponibilidad` después, no reemite el evento si se repite) | `ActividadEvaluativaPeriodoAbierto` no cerrada → `cerrada_manualmente = true`, todas sus `Evaluacion` `EnCurso`/`Suspendida` finalizadas de inmediato |

**Orden de implementación:** US-3.3.1 y US-3.3.2 son independientes entre sí — ambas solo
dependen de la Iteración 2 (read model de evaluaciones activas, Use Case de finalización
reutilizado por la cascada de US-3.3.2).

~~US-3.3.1~~ Issue #163. ~~US-3.3.2~~ Issue #164. Specs en `docs/specs/inc3/US-3.3.1.md`,
`US-3.3.2.md`.

---

## Iteración 4 — Frontend (consume las Iteraciones 1 a 3 completas)

> Mismo criterio que Identidad (backend e Iteración 2 de frontend separadas) y no el de Banco
> de Preguntas (frontend dentro de la misma iteración que su backend): acá el hito de cierre
> del incremento —"un estudiante completa una evaluación de principio a fin... y el docente
> extiende el plazo de una sesión activa"— cruza las tres iteraciones de backend a la vez
> (creación es Iteración 1, rendir/revisar es Iteración 2, extender/cerrar es Iteración 3), así
> que no hay una forma natural de repartir las 12 pantallas del prototipo sin adelantar
> pantallas a iteraciones de backend que todavía no existen. Se difiere el frontend completo a
> una Iteración 4 que consume las tres de una vez.

| US | Descripción | Pantallas (`wireframes-actividad-evaluativa.md`) | Backend consumido | Depende de |
|---|---|---|---|---|
| **US-3.4.1** *(técnica)* | Infraestructura de frontend del BC: rutas de Actividad Evaluativa, cliente API tipado (reutiliza el cliente HTTP con JWT de US-1.1.6) | Sin pantalla propia — soporte técnico | — | US-3.1.1 a US-3.3.2 |
| **US-3.4.2** | Docente ve sus materias y el listado de actividades de una materia | §2.0 `#doc-materias`, §2.1 `#doc-actividades` | `GET /materias` (US-2.1.9, reuso), listado de actividades (a definir sobre US-3.1.2) | US-3.4.1 |
| **US-3.4.3** | Docente crea una nueva actividad de período abierto | §2.2 `#doc-nueva-actividad` | `POST /actividades` (US-3.1.2) | US-3.4.2 |
| **US-3.4.4** | Docente ve el detalle de una actividad, extiende el plazo y la cierra manualmente | §2.3 `#doc-detalle-actividad`, §2.4 `#doc-extender-plazo`, §2.5 `#doc-cerrar-actividad` | detalle de actividad (sobre US-3.1.2), `PUT/PATCH` de modificación (US-3.3.1), `POST` de cierre (US-3.3.2) | US-3.4.3 |
| **US-3.4.5** | Estudiante ve sus materias y las actividades disponibles, incluido el estado "fuera de período" | §3.0 `#est-materias`, §3.1 `#est-actividades`, §3.2 `#est-fuera-periodo` | listado de actividades visibles para la comisión (sobre US-3.1.2) | US-3.4.1 |
| **US-3.4.6** | Estudiante rinde la evaluación: responde, pausa y reanuda | §3.3 `#est-rendir`, §3.4 `#est-suspendida` | `POST /evaluaciones` (US-3.1.3), `POST /evaluaciones/{id}/respuestas` (US-3.2.1), suspender/reanudar (US-3.2.2) | US-3.4.5 |
| **US-3.4.7** | Estudiante finaliza y ve la revisión completa de su evaluación | §3.5 `#est-revision` | `POST /evaluaciones/{id}/finalizar` (US-3.2.3), `GET` de revisión (US-3.2.3) | US-3.4.6 |

**Orden de implementación:** US-3.4.1 primero (bloquea al resto). Lado docente
(US-3.4.2→3.4.3→3.4.4) y lado estudiante (US-3.4.5→3.4.6→3.4.7) pueden avanzar en paralelo —
son independientes entre sí, ambos solo dependen de US-3.4.1.

**Gap de backend detectado al crear las specs (2026-08-28):** la tabla de candidatas asumía
"Iteración 4 = solo frontend, consume las Iteraciones 1 a 3 tal cual" — no es así. Los routers
reales (`actividades_router.py`, `evaluaciones_router.py`) no exponen ningún `GET` de lectura
(listado/detalle de actividades, contenido de pregunta asignada, respuestas ya dadas), y el
lado Estudiante no tiene ningún endpoint propio fuera de login/registro/password. Decisión de
Víctor: cada US que lo necesite extiende el backend mínimo dentro de su propio alcance (mismo
criterio que `US-2.1.9`/`US-2.2.8`), documentado en el spec de cada una — no se abre una
iteración técnica aparte. Afecta a `US-3.4.2`, `US-3.4.4`, `US-3.4.5` y `US-3.4.6`.

~~US-3.4.1~~ Issue #170. ~~US-3.4.2~~ Issue #171. ~~US-3.4.3~~ Issue #172. ~~US-3.4.4~~ Issue
#173. ~~US-3.4.5~~ Issue #174. ~~US-3.4.6~~ Issue #175. ~~US-3.4.7~~ Issue #176. Specs en
`docs/specs/inc3/US-3.4.1.md` a `US-3.4.7.md`.

---

## DoD del Incremento (hito, `PLAN_v1.md`)

> Un estudiante completa una evaluación de período abierto de principio a fin —incluida una
> desconexión simulada para validar cero pérdida de respuestas— y el docente extiende el plazo
> de una sesión activa.

Se verifica de punta a punta en UAT (Capa 1 pytest + Capa 2 HTTP, más el navegador real para el
frontend) al cierre del incremento, según `PROCEDIMIENTO-UAT.md` — no basta con que cada US
individual pase sus propios tests. La desconexión simulada (RNF Confiabilidad) se ejercita
confirmando una `Respuesta` y verificando que sobrevive a un reinicio del proceso backend antes
de la siguiente confirmación (INV-AE-09).

---

## Próximos pasos

1. ~~Crear GitHub Issues (Milestone `Incremento 3 — Sesión de Período Abierto`, labels
   `us-iedd`, `incremento-3`, `tipo:modelado`) para US-3.0.1 y US-3.0.2.~~ Creados 2026-08-24:
   Issue #137 (US-3.0.1), Issue #138 (US-3.0.2). Las US tipo `Modelado` no generan spec en
   `docs/specs/` — el propio Issue es la spec completa (a diferencia de las US tipo `feature`
   de Iteración 1+, mismo criterio que `inc1-candidatas.md`/`inc2-candidatas.md`).
2. ~~Ejecutar el event storming (US-3.0.1) y los wireframes (US-3.0.2), con aprobación explícita
   de Víctor en cada Issue.~~ Hecho.
3. ~~Al cerrar la Iteración 0: actualizar este archivo con el detalle completo de comandos/
   eventos de las Iteraciones 1 a 3, mismo formato que `inc2-candidatas.md`.~~ Hecho — este
   archivo, más una Iteración 4 de frontend.
4. Revisar esta tabla de candidatas contigo antes de crear Issues/specs — en particular: el
   agrupamiento de `CerrarActividad` en la Iteración 3 (no mapea a un RF propio), la separación
   de la infraestructura de Event Sourcing en `US-3.1.1`, el `VerificadorDeVencimientos` como
   `US-3.2.4`, y la decisión de diferir todo el frontend a una Iteración 4 en vez de intercalarlo
   con cada iteración de backend (a diferencia de Banco de Preguntas).
5. ~~Crear GitHub Issues (Milestone `Incremento 3 — Sesión de Período Abierto`) y
   `docs/specs/inc3/US-3.M.K.md` por cada US aprobada.~~ Hecho para Iteraciones 1 a 3
   (backend) y, 2026-08-28, para la Iteración 4 (frontend) — Issues #170 a #176.
6. Implementar Iteración 1 → 2 → 3 (backend, en ese orden — cada una depende de la anterior) →
   Iteración 4 (frontend, en curso).
