# HITO-7 — Dos hallazgos bloqueantes en la UAT de cierre de la Iteración 4: validación de intersección entre USs y concurrencia real no traducida

> Estado documental: evidencia
> Registra un hallazgo de aprendizaje del ensayo IEDD en Cognion.
> No reemplaza a las fuentes vigentes (ADRs, arquitectura, specs).

| Campo | Valor |
|-------|-------|
| **Documento** | HITO-7 — dos hallazgos bloqueantes de naturaleza distinta en la misma UAT |
| **Fecha** | 2026-08-31 |
| **Incremento / contexto** | Incremento 3 (Actividad Evaluativa), UAT de cierre de la Iteración 4 — primer recorrido de punta a punta con frontend real (Docente + Estudiante) |
| **Relacionado** | `US-3.1.3`, `US-3.3.2`, `US-ADJ-11`, Issue [#192](https://github.com/vvalotto/cognion/issues/192), PRs [#193](https://github.com/vvalotto/cognion/pull/193)/[#194](https://github.com/vvalotto/cognion/pull/194), `quality/reports/uat/inc3/evidencia-iter4.md` |

---

## Contexto

La Iteración 4 del Incremento 3 integró por primera vez, con frontend real, tres iteraciones
de backend cerradas por separado (`US-3.1.*`, `US-3.2.*`, `US-3.3.*`), cada una con su propia
suite de tests aprobada en su momento. La UAT de cierre debía verificar el DoD completo del
incremento: un Estudiante completa una evaluación de principio a fin (incluida una desconexión
simulada) y un Docente extiende o cierra el plazo de una actividad. Se extendió `smoke.sh`
(Capa 2, HTTP) con el tramo de Iteraciones 2 y 3 que nunca se había ejercitado end-to-end, y se
hizo un recorrido manual completo en navegador real (Docente + Estudiante). Ambos caminos
encontraron, cada uno, un hallazgo 🔴 Bloqueante — de naturaleza completamente distinta entre
sí, aunque los dos en el mismo Use Case (`IniciarEvaluacionUseCase`).

---

## Hallazgo A — `IniciarEvaluacion` no rechazaba una actividad cerrada manualmente

### Cómo se detectó

Extendiendo `smoke.sh` (Capa 2) con el tramo de `US-3.3.1`/`US-3.3.2` (extender plazo, cerrar
actividad) — nunca antes ejercitado end-to-end vía HTTP. El paso "un Estudiante sin
`Evaluacion` previa intenta iniciar sobre una actividad recién cerrada manualmente" devolvió
`200` en vez del `422` esperado.

### Causa raíz

`IniciarEvaluacionUseCase.execute()` (`US-3.1.3`, escrito antes de que existiera el cierre
manual) solo validaba la ventana de fechas (`ahora < apertura or ahora > cierre`). Cuando
`US-3.3.2` agregó `cerrada_manualmente` como estado terminal de la actividad, nadie volvió a
tocar ese chequeo — a pesar de que el propio docstring de la excepción `FueraDePeriodo` ya
decía, desde `US-3.1.3`: *"ahora no está dentro de la ventana vigente de la actividad, o está
cerrada manualmente"*. La intención estaba documentada; la implementación nunca la siguió.

Ningún test la había cubierto porque el escenario vive exactamente en la intersección de dos
USs escritas en momentos distintos: los BDD de `US-3.3.2` verifican el comportamiento de
*cerrar* (que sea terminal, que finalice en cascada a quienes ya estaban rindiendo — INV-AE-04b),
no vuelven a poner a prueba `IniciarEvaluacion`, que ya estaba cerrada y aprobada semanas antes.

### Cómo se resolvió

`US-ADJ-11`, Issue #192, PR #193: una línea — agregar `or actividad.cerrada_manualmente` a la
condición que levanta `FueraDePeriodo`. Sin cambios de frontend (el 422 ya redirige a
`#est-fuera-periodo` desde `US-3.4.5`). Test unitario nuevo + verificación end-to-end contra el
backend real (`smoke.sh` y, después, el recorrido manual en navegador).

---

## Hallazgo B — carrera real de concurrencia en `IniciarEvaluacion`

### Cómo se detectó

En el recorrido manual en navegador (no en ningún test automatizado): al entrar como
Estudiante a "Rendir evaluación", la pantalla quedaba colgada en "Cargando…" indefinidamente.
Inspeccionando la red del navegador se vieron **dos** `POST /evaluaciones` disparados casi
simultáneos — uno `200 OK`, el otro `500`. La causa: React StrictMode (activo en `main.tsx`,
comportamiento estándar de desarrollo) invoca el `useEffect` de montaje dos veces, disparando
dos peticiones reales concurrentes.

### Causa raíz

Las dos peticiones concurrentes llegan al mismo tiempo a "no existe evaluación todavía" y
ambas intentan insertar el primer evento (`EvaluacionIniciada`) del mismo stream. Una gana, la
otra choca contra el índice único de la tabla `events`
(`uq_events_stream_sequence`) — pero `SQLAlchemyEventStore.append()` nunca traducía esa
violación real de Postgres en el error de dominio esperado (`ConcurrenciaOptimistaError`); la
dejaba subir cruda hasta un `500` genérico. El propio docstring de la clase ya decía que ese
índice único era *"el respaldo ante una escritura concurrente genuina entre dos transacciones
distintas"* — la pieza estaba diseñada, nunca conectada.

Es un tipo de bug estructuralmente distinto del Hallazgo A: no es una validación de negocio
incompleta, es una condición de carrera en la capa de persistencia. Los escenarios BDD
(Given-When-Then) son secuenciales por construcción — no existe una forma natural de expresar
"dos peticiones llegan exactamente al mismo instante" en ese formato sin un test de
concurrencia dedicado, que nadie tenía motivo de escribir hasta que el síntoma apareció.

### Cómo se resolvió

Misma US-ADJ-11 (alcance ampliado), PR #194: `SQLAlchemyEventStore.append()` captura la
`IntegrityError` del `commit()` y la traduce en `ConcurrenciaOptimistaError`;
`IniciarEvaluacionUseCase` la captura al insertar el primer evento y relee el stream para
devolver la `Evaluacion` que ganó la carrera, en vez de propagar el error. Verificado con un
test de integración real usando `asyncio.gather` (dos `POST /evaluaciones` simultáneos contra
Postgres real) — reproduce la carrera de forma determinística, no depende de timing frágil.
Reverificado también repitiendo el recorrido manual completo en navegador después del fix.

---

## Aprendizaje(s)

- **L-7.1:** Cuando una US nueva introduce un estado que puede interactuar con el flujo
  "feliz" de una US ya cerrada (acá: `cerrada_manualmente` de `US-3.3.2` afectando a
  `IniciarEvaluacion` de `US-3.1.3`), esa intersección no aparece sola en los BDD de la US
  nueva — hay que preguntarla explícitamente: *"¿este estado nuevo invalida algo que otro Use
  Case ya daba por asumido?"*. Cuando el código mismo ya documenta la intención (como el
  docstring de `FueraDePeriodo` acá), esa pregunta tiene una respuesta barata: grep del
  docstring contra el comportamiento real antes de cerrar la US que lo introduce.
- **L-7.2:** Los bugs de concurrencia real casi nunca los atrapa una suite BDD secuencial —
  necesitan una categoría de test aparte (concurrencia explícita, ej. `asyncio.gather`) o
  aparecen recién en uso interactivo real. Es razonable — no un fallo del proceso de testing —
  que este tipo de hallazgo emerja en la UAT manual y no antes.
- **L-7.3:** Ambos bugs compartían una misma forma: el código *ya sabía* qué tenía que pasar
  (documentado en un docstring) pero esa intención nunca se conectó a una ejecución real. Vale
  la pena, al revisar código, tratar un docstring que promete un comportamiento no cubierto por
  ningún test como una señal de alerta en sí misma — no solo documentación, sino una promesa
  sin verificar.

---

## Relación con la hipótesis del ensayo

Coincide con el patrón ya señalado en `HITO-6`: ni la revisión de código ni una suite de tests
con fixtures mínimos sustituyen una UAT de punta a punta con datos e interacción reales. Acá el
matiz es distinto — no fue un problema de volumen de datos, fue de **secuencia temporal entre
USs** (Hallazgo A) y de **concurrencia real** (Hallazgo B), dos dimensiones que un pipeline de
tests secuenciales, por más completo que sea, no ejercita por diseño. El ensayo IEDD asume que
UAT + revisión humana cierran ese gap — este HITO es evidencia de que, ambas veces, así fue:
los dos hallazgos se detectaron y resolvieron en la misma sesión de UAT, antes de dar el
Incremento por cerrado.

---

## Resumen de Aprendizajes

| ID | Aprendizaje | Impacto |
|----|-------------|---------|
| L-7.1 | Un estado nuevo que interactúa con un Use Case de una US ya cerrada necesita una pregunta explícita de intersección — no aparece solo en los BDD de la US nueva | Proceso / Workflow |
| L-7.2 | Los bugs de concurrencia real requieren tests dedicados (o UAT interactiva) — una suite BDD secuencial no los atrapa por diseño | Quality Gates / Testing |
| L-7.3 | Un docstring que promete un comportamiento sin test que lo cubra es una señal de alerta a tratar como tal en revisión de código | Proceso / Quality |

---

*Creado: 2026-08-31*
