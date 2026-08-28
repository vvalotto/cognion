# BC Actividad Evaluativa — Modelo de Dominio (Event Storming)

> Estado documental: **borrador — pendiente de aprobación explícita de Víctor en el comentario
> de cierre del Issue #137 (US-3.0.1, Iteración 0, Incremento 3).**
> Alcance de este modelo: exclusivamente el modo **período abierto** (RF-11, RF-11b, RF-12,
> RF-13). El modo **en vivo** (RF-08 a RF-10) y las notificaciones (RF-14) no forman parte de
> este incremento (`docs/plans/inc3/inc3-candidatas.md`) — quedan fuera de alcance de este
> documento.
>
> Fuente: `docs/rf/RF_v1.md` (RF-11, RF-11b, RF-12, RF-13), `docs/rf/RNF_v1.md` (Confiabilidad
> — escenario de interrupción durante sesión de período abierto), `ADR-002` (Event Sourcing +
> CQRS, Aceptado), `ADR-009` (Unit of Work por Use Case, Aceptado), `ADR-015` (BC renombrado de
> "Sesiones" a "Actividad Evaluativa" — el agregado y los eventos de dominio también se
> renombran, Aceptado), `docs/architecture/03-bounded-contexts.md` §Actividad Evaluativa.
> Modelado en conversación con Víctor, 2026-08-25.
> Diagramas complementarios (estructura de aggregates + ciclo de vida de `Evaluacion` y de
> `ActividadEvaluativaPeriodoAbierto`, en Mermaid): `BC-actividad-evaluativa-modelo-diagramas.html`.
> Event storming en línea de tiempo (comandos/eventos por actor, incluida la Policy
> `VerificadorDeVencimientos`): `BC-actividad-evaluativa-modelo-event-storming.html`.
>
> **Nota de terminología (corrige el Issue #137):** el Issue lista los eventos `SesionCreada` y
> `SesionCerrada`, redactados antes del renombre. `ADR-015` ya estableció que el agregado
> administrado por el docente se llama `ActividadEvaluativaPeriodoAbierto` y sus eventos
> `ActividadEvaluativaCreada`/`ActividadEvaluativaCerrada` — este documento usa la terminología
> del ADR, no la del Issue original.

---

## 1. Actores

| Actor | Rol en el BC |
|---|---|
| Docente | Crea la actividad de período abierto (materia, ventana de disponibilidad, cantidad de preguntas, cantidad de intentos por respuesta), y puede extender el plazo mientras está vigente |
| Estudiante | Inicia su propia `Evaluacion` dentro de una actividad, responde preguntas (con reintentos si la actividad lo permite), puede suspenderla y reanudarla, y la finaliza |
| Sistema | Suspende automáticamente una `Evaluacion` `EnCurso` sin actividad por un tiempo configurable, y finaliza automáticamente lo que sigue `EnCurso`/`Suspendida` al llegar `fecha_cierre` (§8) |

---

## 2. Concepto central — dos aggregates, no uno

Hot spot resuelto en la sesión de modelado: inicialmente se consideró un único aggregate por
actividad que acumulara el estado de todos los estudiantes. Se descartó — con 30 a 60 alumnos
respondiendo, ese aggregate crecería sin límite y cada respuesta individual tocaría el mismo
stream de eventos que el resto de la clase (mismo criterio que separó `PreguntaPlantilla` de
`Banco` en `BC-banco-preguntas-modelo.md` §5, punto 3).

El modelo tiene **dos aggregates independientes, cada uno con su propio stream de eventos**:

1. **`ActividadEvaluativaPeriodoAbierto`** (dueño: Docente) — la ventana de disponibilidad y sus
   parámetros. Un aggregate por actividad creada.
2. **`Evaluacion`** (dueño: Estudiante) — el recorrido de un estudiante particular dentro de una
   actividad: el set de preguntas que le tocó y sus respuestas. Un aggregate por
   `(actividad_id, estudiante_id)`.

**Relación entre ambos:** `Evaluacion` referencia `actividad_id`, pero no hay invariante que se
verifique cargando ambos aggregates juntos en memoria — el único invariante cruzado (RF-11b, no
acortar el período con evaluaciones en curso) se resuelve consultando un **read model** de
"evaluaciones en curso por actividad" antes de aceptar el comando, no cargando el aggregate
`Evaluacion` de cada estudiante (CQRS, `ADR-002`).

**Terminología:**
- **`Evaluacion`** — término **nuevo**, introducido en este modelado (a incorporar al lenguaje
  ubicuo de `docs/architecture/03-bounded-contexts.md` cuando se apruebe). El recorrido de un
  estudiante dentro de una actividad de período abierto. Deliberadamente no se llama "Sesión"
  (`ADR-015`).
- **`Respuesta`** — término **ya existente** en el lenguaje ubicuo
  (`docs/architecture/03-bounded-contexts.md` §Actividad Evaluativa lo lista desde antes de
  este modelado; `ADR-015` ya fijó el nombre del evento `RespuestaRegistrada` sin cambios). Es
  **Entity, no Value Object** (corrección de una versión previa de este documento, a pedido de
  Víctor): cada confirmación de una respuesta a una `PreguntaAsignada` es un hecho único e
  irrepetible del dominio — tiene identidad propia (`id`), es inmutable una vez creada, y vive
  en una colección de primer nivel dentro de `Evaluacion` (§5), no anidada dos niveles adentro.
  Un estudiante puede tener varias `Respuesta` para la misma `PreguntaAsignada` si la actividad
  permite más de un intento (RF-11, `cantidad_intentos_permitidos`) — cada una es una `Respuesta`
  distinta con su propio `id`, no una edición de la anterior.

---

## 3. Línea de tiempo — Eventos de dominio

Orden narrativo, no técnico. 🟧 evento de dominio · 🟦 comando · 🟨 aggregate.

```
[Docente]
   |
🟦 CrearActividadPeriodoAbierto(materia_id, fecha_apertura, fecha_cierre,
                                 cantidad_preguntas, cantidad_intentos_permitidos)
   |
🟧 ActividadEvaluativaCreada                              🟨 ActividadEvaluativaPeriodoAbierto
   |
🟦 ModificarPeriodoDisponibilidad(actividad_id, nueva_fecha_cierre)
   |
🟧 PeriodoDisponibilidadModificado                         🟨 ActividadEvaluativaPeriodoAbierto
   |
🟦 CerrarActividad(actividad_id)          — opcional, decisión del docente, antes de fecha_cierre
   |
🟧 ActividadEvaluativaCerrada             (terminal — finaliza en cascada las Evaluacion
   |                                        activas, §6b Regla 2 ampliada)  🟨 ActividadEvaluativaPeriodoAbierto

[Estudiante]
   |
🟦 IniciarEvaluacion(actividad_id, estudiante_id)
   |
🟧 EvaluacionIniciada          (fija el set de PreguntaAsignada — RF-12)   🟨 Evaluacion
   |
🟦 RegistrarRespuesta(evaluacion_id, pregunta_id, respuesta)
   |
🟧 RespuestaRegistrada          (persistencia atómica, respuesta a respuesta —      🟨 Evaluacion
   |                             crea una nueva Respuesta, entidad con id propio)
   |                            (se repite por cada pregunta, y más de una vez
   |                             por pregunta si cantidad_intentos_permitidos > 1 —
   |                             cada repetición es una Respuesta distinta, no una edición)
   |
🟦 SuspenderEvaluacion(evaluacion_id)              — Estudiante o Sistema (inactividad)
   |
🟧 EvaluacionSuspendida                                                    🟨 Evaluacion
   |
🟦 ReanudarEvaluacion(evaluacion_id)                — Estudiante, explícito
   |
🟧 EvaluacionReanudada          (vuelve a EnCurso, mismo set y respuestas) 🟨 Evaluacion
   |
🟦 FinalizarEvaluacion(evaluacion_id)                — Estudiante, o Sistema al llegar fecha_cierre
   |
🟧 EvaluacionFinalizada         (habilita la revisión — RF-13)             🟨 Evaluacion


[⏰ VerificadorDeVencimientos — Policy, no es un aggregate, ver §6b]
   |
   (corre periódicamente, sin comando de un actor humano — dispara sobre lo que encuentra
    vencido en los read models)
   |
   Regla 1 — inactividad: Evaluacion EnCurso sin actividad hace > umbral configurado
   |
🟦 SuspenderEvaluacion(evaluacion_id)   — emitido por la Policy, actor = Sistema
   |
🟧 EvaluacionSuspendida
   |
   Regla 2 — vencimiento del período: ActividadEvaluativaPeriodoAbierto con fecha_cierre pasada
   |
🟦 FinalizarEvaluacion(evaluacion_id)   — emitido por la Policy, una vez por cada Evaluacion
   |                                      EnCurso/Suspendida de esa actividad
🟧 EvaluacionFinalizada
```

**Reconexión simple (RNF Confiabilidad) vs. suspensión (deliberada):** son dos mecanismos
distintos. `IniciarEvaluacion` sigue siendo idempotente — si ya existe una `Evaluacion`
`EnCurso`, una reconexión que no pasó por `Suspendida` la retoma sin eventos adicionales, mismo
set de `PreguntaAsignada` visible. `SuspenderEvaluacion`/`EvaluacionSuspendida` en cambio
registra explícitamente una pausa (por decisión del estudiante o por inactividad detectada por
el Sistema) — queda en el event store como parte de la trazabilidad de la evaluación (RNF
Observabilidad), y requiere `ReanudarEvaluacion` explícito antes de poder volver a
`RegistrarRespuesta` (§8).

**Los eventos `EvaluacionSuspendida`/`EvaluacionFinalizada` son el mismo hecho de dominio sin
importar quién lo disparó** (estudiante o `VerificadorDeVencimientos`) — el payload distingue el
actor (`estudiante` vs `sistema`) para trazabilidad, pero no son eventos distintos: es el mismo
invariante (INV-AE-11/12, INV-AE-04) el que se cumple en ambos casos. Lo que faltaba modelar era
el disparador automático — ver §6b.

**`CerrarActividad` es una medida opcional del docente, no un paso obligatorio del ciclo de
vida** — la mayoría de las actividades probablemente nunca lo usan y simplemente llegan a
`fecha_cierre` naturalmente (disparando la Regla 2 del `VerificadorDeVencimientos`, §6b). Existe
para el caso en que el docente quiere terminar la actividad antes de lo planeado (ej. ya
respondieron todos, o se decidió invalidarla). A diferencia de llegar pasivamente a
`fecha_cierre`, es una decisión deliberada y terminal: finaliza en cascada las `Evaluacion`
activas de inmediato (mismo efecto que la Regla 2) y no admite reabrir con
`ModificarPeriodoDisponibilidad` después (INV-AE-04b, §5).

---

## 4. Comandos → Eventos

| Comando | Actor | Aggregate | Evento(s) | Excepciones |
|---|---|---|---|---|
| `CrearActividadPeriodoAbierto(materia_id, fecha_apertura, fecha_cierre, cantidad_preguntas, cantidad_intentos_permitidos)` | Docente | `ActividadEvaluativaPeriodoAbierto` (crea) | `ActividadEvaluativaCreada` | `MateriaNoExiste`, `PeriodoInvalido` (INV-AE-02), `CantidadIntentosInvalida` (INV-AE-03), `PreguntasInsuficientes` (INV-AE-01) |
| `ModificarPeriodoDisponibilidad(actividad_id, nueva_fecha_cierre)` | Docente | `ActividadEvaluativaPeriodoAbierto` (modifica) | `PeriodoDisponibilidadModificado` | `ActividadNoExiste`, `PeriodoInvalido`, `NoSePuedeAcortarConEvaluacionesActivas` (INV-AE-04, RF-11b), `ActividadYaCerrada` (INV-AE-04b) |
| `CerrarActividad(actividad_id)` — **opcional** | Docente | `ActividadEvaluativaPeriodoAbierto` (cierra, terminal) | `ActividadEvaluativaCerrada` | `ActividadNoExiste`, `ActividadYaCerrada` |
| `IniciarEvaluacion(actividad_id, estudiante_id)` | Estudiante | `Evaluacion` (crea, o retoma si ya existe una en curso — idempotente) | `EvaluacionIniciada` | `ActividadNoExiste`, `FueraDePeriodo` (antes de `fecha_apertura`, después de `fecha_cierre` vigente, o actividad cerrada manualmente) |
| `RegistrarRespuesta(evaluacion_id, pregunta_id, respuesta)` | Estudiante | `Evaluacion` (agrega una `Respuesta` nueva a la colección) | `RespuestaRegistrada` | `EvaluacionNoExiste`, `EvaluacionYaFinalizada`, `EvaluacionSuspendida` (INV-AE-12), `PreguntaNoAsignada` (INV-AE-07), `IntentosAgotados` (INV-AE-08), `FueraDePeriodo` |
| `SuspenderEvaluacion(evaluacion_id)` | Estudiante, o Sistema tras un período de inactividad configurable | `Evaluacion` (suspende) | `EvaluacionSuspendida` | `EvaluacionNoExiste`, `EvaluacionYaFinalizada`, `EvaluacionYaSuspendida` |
| `ReanudarEvaluacion(evaluacion_id)` | Estudiante | `Evaluacion` (reanuda) | `EvaluacionReanudada` | `EvaluacionNoExiste`, `EvaluacionYaFinalizada` (INV-AE-11), `EvaluacionNoSuspendida`, `FueraDePeriodo` |
| `FinalizarEvaluacion(evaluacion_id)` | Estudiante, o Sistema al llegar `fecha_cierre` sobre lo que siga `EnCurso`/`Suspendida` | `Evaluacion` (finaliza) | `EvaluacionFinalizada` | `EvaluacionNoExiste`, `EvaluacionYaFinalizada` |

**Query — sin comando ni evento de dominio:**

| Query | Actor | Fuente | Resultado |
|---|---|---|---|
| `ObtenerRevisionEvaluacion(evaluacion_id)` | Estudiante | `Evaluacion` finalizada (read model) | Detalle por pregunta: respuesta propia, correcta/incorrecta, respuesta correcta si falló (RF-13) |
| `ContarEvaluacionesActivas(actividad_id)` | — (uso interno de `ModificarPeriodoDisponibilidad`) | read model `evaluaciones_activas_por_actividad` | Cantidad de `Evaluacion` en `EnCurso` o `Suspendida` (no `Finalizada`) para esa actividad — sostiene INV-AE-04 |
| `ListarEvaluacionesInactivasDesde(umbral)` | — (uso interno del `VerificadorDeVencimientos`, §6b) | read model `evaluaciones_activas_por_actividad` | `Evaluacion` en `EnCurso` cuya `ultima_actividad_en` supera el umbral configurado |
| `ListarEvaluacionesDeActividadesVencidas()` | — (uso interno del `VerificadorDeVencimientos`, §6b) | read model `evaluaciones_activas_por_actividad` + `ActividadEvaluativaPeriodoAbierto.fecha_cierre` | `Evaluacion` en `EnCurso`/`Suspendida` cuya actividad ya tiene `fecha_cierre` pasada |

---

## 5. Aggregates

### `ActividadEvaluativaPeriodoAbierto` (Aggregate Root)

| Atributo | Tipo | Notas |
|---|---|---|
| `id` | UUID | |
| `materia_id` | referencia a `Materia` (BC Banco de Preguntas) | vía puerto propio, sin import directo (`CLAUDE.md`) |
| `fecha_apertura` | datetime | |
| `fecha_cierre` | datetime | mutable — cambia con `ModificarPeriodoDisponibilidad` mientras no esté cerrada manualmente |
| `cantidad_preguntas` | int | tamaño del set que recibe cada estudiante (RF-11, RF-12) |
| `cantidad_intentos_permitidos` | int | por defecto 1 (RF-11) — tope de `Respuesta` por `PreguntaAsignada`, no de reintentos de la evaluación completa |
| `cerrada_manualmente` | bool | `false` por defecto; `true` tras `ActividadEvaluativaCerrada` — terminal, ver INV-AE-04b |

**Invariantes:**
- **INV-AE-01:** `cantidad_preguntas` ≤ cantidad de `PreguntaPlantilla` activas de la materia al
  momento de crear la actividad (consulta a BC Banco de Preguntas vía puerto).
- **INV-AE-02:** `fecha_apertura` < `fecha_cierre` (se revalida en cada modificación, contra la
  `nueva_fecha_cierre`).
- **INV-AE-03:** `cantidad_intentos_permitidos` ≥ 1.
- **INV-AE-04:** `ModificarPeriodoDisponibilidad` con `nueva_fecha_cierre` < `fecha_cierre`
  actual (acortar) se rechaza si existe alguna `Evaluacion` **activa** (`EnCurso` o
  `Suspendida` — no `Finalizada`) para esta actividad (`NoSePuedeAcortarConEvaluacionesActivas`,
  RF-11b caso límite). Una `Suspendida` sigue siendo "estudiante activo" a este efecto — puede
  reanudar y seguir respondiendo, `ReanudarEvaluacion` (INV-AE-11) no genera un intento nuevo de
  `IniciarEvaluacion`. Extender (`nueva_fecha_cierre` > actual) no tiene esta restricción.
- **INV-AE-04b:** `CerrarActividad` es terminal — una vez `cerrada_manualmente = true`,
  `ModificarPeriodoDisponibilidad` se rechaza (`ActividadYaCerrada`) y `CerrarActividad` de
  nuevo también (no reemite el evento). A diferencia de INV-AE-04, `CerrarActividad` **no**
  requiere ausencia de `Evaluacion` activas — es justamente la vía para terminar la actividad
  con estudiantes todavía respondiendo (§6b, Regla 2 ampliada la finaliza en cascada). No admite
  reabrir: es una decisión deliberada del docente, a diferencia de llegar pasivamente a
  `fecha_cierre` (que sí admite extensión — cubre el escenario de caída del sistema, §8.2).

**Sin estado propio de las evaluaciones de los estudiantes** — ver §2. El aggregate no crece con
la cantidad de alumnos ni de respuestas.

**Nota de implementación (`US-3.3.1`, 2026-08-28):** `ModificarPeriodoDisponibilidad`
(INV-AE-02/04/04b) implementada — primer comando que agrega un segundo evento posible
(`PeriodoDisponibilidadModificado`) al stream de esta actividad, que hasta acá siempre tenía un
único evento (`ActividadEvaluativaCreada`). Introduce `ActividadEvaluativaPeriodoAbierto.
reconstruir()` (replay real, mismo patrón de dispatch por `event_type` que
`Evaluacion.reconstruir()`/`_aplicar_evento`, `US-3.2.2`) — consecuencia obligatoria: los 4 Use
Case que hasta `US-3.2.4` leían `fecha_apertura`/`fecha_cierre`/`cantidad_preguntas` directamente
del primer evento del stream (`IniciarEvaluacion`, `RegistrarRespuesta`, `ReanudarEvaluacion`, y
la Regla 2 del `VerificadorDeVencimientos`) pasan a usar `reconstruir()`, para que una extensión
o acortamiento del plazo sea visible en el resto del BC. `CerrarActividad` (INV-AE-04b, Regla 3)
implementada en `US-3.3.2` (nota abajo, §6b) — cierra la Iteración 3 del Incremento 3 (backend).

**Nota de implementación (`US-3.3.2`, 2026-08-28):** `CerrarActividad` implementada —
tercer evento posible del stream (`ActividadEvaluativaCerrada`), rama nueva en `_aplicar_evento`
(`cerrada_manualmente = True`) y `validar_para_cerrar()` (INV-AE-04b, sin otra restricción: a
diferencia de INV-AE-04 no requiere ausencia de `Evaluacion` activas). La cascada síncrona
(Regla 3, §6b) vive en `CerrarActividadUseCase`: emite el evento y, en la misma invocación,
reutiliza `FinalizarEvaluacionUseCase` con `actor="sistema"` (mecanismo introducido en
`US-3.2.4`) por cada `Evaluacion` activa de la actividad, sin esperar la próxima pasada del job
periódico.

### `Evaluacion` (Aggregate Root)

| Atributo | Tipo | Notas |
|---|---|---|
| `id` | UUID | |
| `actividad_id` | referencia a `ActividadEvaluativaPeriodoAbierto` | |
| `estudiante_id` | referencia a `Usuario` (BC Identidad) | vía puerto propio, mismo criterio que `materia_id` |
| `preguntas_asignadas` | lista de `PreguntaAsignada` (Value Object) | fijada por completo en `EvaluacionIniciada` — inmutable en cantidad y orden (INV-AE-05) |
| `respuestas` | colección de `Respuesta` (**Entity**, id propio) | crece con cada `RespuestaRegistrada` — nunca se edita ni se borra una `Respuesta` existente, solo se agregan nuevas (§2, corrección de nomenclatura) |
| `estado` | `EnCurso \| Suspendida \| Finalizada` | |
| `iniciada_en` | datetime | |
| `finalizada_en` | datetime \| None | |

**Invariantes:**
- **INV-AE-05:** el set de `PreguntaAsignada` es fijo desde `EvaluacionIniciada` — reconectarse
  retoma la `Evaluacion` existente, nunca genera un set nuevo (RNF Confiabilidad, "el estudiante
  no puede obtener un nuevo set reconectándose").
- **INV-AE-06:** a lo sumo una `Evaluacion` en curso por `(actividad_id, estudiante_id)` —
  `IniciarEvaluacion` es idempotente si ya existe una en curso para ese par.
- **INV-AE-07:** `RegistrarRespuesta` requiere que `pregunta_id` pertenezca al set de
  `preguntas_asignadas`, que la `Evaluacion` esté `EnCurso`, y que la actividad esté dentro de
  su período vigente (`fecha_apertura` ≤ ahora ≤ `fecha_cierre` vigente — incluida cualquier
  extensión de RF-11b).
- **INV-AE-08:** la cantidad de `Respuesta` ya registradas para una `PreguntaAsignada` (mismo
  `pregunta_id`) no puede superar `cantidad_intentos_permitidos` de la actividad
  (`IntentosAgotados` si se excede).
- **INV-AE-09 (persistencia atómica, RNF Confiabilidad):** cada `Respuesta` se crea y persiste
  en su propia transacción al momento de la confirmación (`ADR-009`, Unit of Work por Use Case)
  — cero pérdida ante desconexión inmediatamente después de confirmar. Es una entidad
  **inmutable**: una vez creada, ninguna `Respuesta` se modifica ni se borra. La **más reciente**
  (`confirmada_en` mayor) de cada `pregunta_id` es la que cuenta como respuesta vigente de esa
  pregunta, tanto para el puntaje como para la revisión (RF-13) — las anteriores quedan en la
  colección y en el event store (auditables, cada una con su propio `id`), pero no participan
  del resultado.
- **INV-AE-10:** la corrección (`es_correcta`) de cada `Respuesta` se calcula y graba en el
  momento en que se crea esa entidad, comparando contra el estado de la `PreguntaPlantilla` (BC
  Banco de Preguntas) en ese instante — es inmutable a ediciones posteriores de esa pregunta en
  el banco (consistente con que `Respuesta` nunca se modifica, INV-AE-09). Sin esto, editar una
  pregunta después de que un estudiante ya respondió alteraría retroactivamente evaluaciones ya
  cerradas.
- **INV-AE-11:** `ReanudarEvaluacion` solo es válido sobre una `Evaluacion` `Suspendida` — una
  `Finalizada` no se puede reanudar (`EvaluacionYaFinalizada`), ni una `EnCurso`
  (`EvaluacionNoSuspendida`, no hay nada que reanudar).
- **INV-AE-12:** `RegistrarRespuesta` requiere `estado = EnCurso` — sobre una
  `Suspendida` se rechaza con `EvaluacionSuspendida`; el estudiante debe `ReanudarEvaluacion`
  primero (INV-AE-11).

**Sin feedback inmediato (hot spot resuelto):** `RegistrarRespuesta` no informa al
estudiante si acertó — coherente con RF-13 ("el detalle completo es visible inmediatamente al
finalizar, no antes"). El estudiante solo sabe cuáles preguntas falló al `FinalizarEvaluacion`.

### Entities / Value Objects internos de `Evaluacion`

**`PreguntaAsignada`** (Value Object, dentro de `preguntas_asignadas`) — sin identidad propia,
solo referencia qué preguntas le tocaron a este estudiante y en qué orden; no acumula estado
propio (a diferencia de una versión previa de este documento, que anidaba ahí los intentos):

| Atributo | Tipo | Notas |
|---|---|---|
| `pregunta_id` | referencia a `PreguntaPlantilla` (BC Banco de Preguntas) | |
| `orden` | int | posición dentro del set — RF-12 no exige un orden fijo de presentación, se conserva por trazabilidad |

**`Respuesta`** (**Entity**, colección de primer nivel dentro de `Evaluacion` — `respuestas`,
no anidada bajo `PreguntaAsignada`): término del lenguaje ubicuo ya existente, ahora modelado
con identidad propia, un hecho único e irrepetible por cada confirmación del estudiante (§2):

| Atributo | Tipo | Notas |
|---|---|---|
| `id` | UUID | identidad propia — lo que la hace Entity y no Value Object |
| `pregunta_id` | referencia a `PreguntaPlantilla` (BC Banco de Preguntas) | debe estar en `preguntas_asignadas` de la misma `Evaluacion` (INV-AE-07) |
| `numero_intento` | int (1..N) | 1ra, 2da, ... confirmación para ese `pregunta_id` — sostiene INV-AE-08 junto con el conteo por `pregunta_id` |
| `contenido` | forma según tipo de pregunta (opción elegida / verdadero-falso) | mismo shape que la `PreguntaPlantilla` correspondiente |
| `es_correcta` | bool | calculada al momento de crear esta `Respuesta` (INV-AE-10) — inmutable después |
| `confirmada_en` | datetime | determina cuál `Respuesta` es la vigente por `pregunta_id` (INV-AE-09) |

---

## 6. Diseño del event store append-only (CQRS)

Extiende `ADR-002` (decisión ya tomada de usar Event Sourcing + CQRS para este BC) con el
diseño concreto que pide el Issue #137:

- **Tabla única `events`** (JSONB, PostgreSQL — `ADR-004`), compartida por ambos tipos de
  aggregate de este BC. Columnas: `id` (PK), `aggregate_type`
  (`"ActividadEvaluativaPeriodoAbierto" | "Evaluacion"`), `aggregate_id` (UUID),
  `sequence_number` (int, orden dentro del stream del aggregate), `event_type` (str), `payload`
  (JSONB), `occurred_at` (timestamptz).
- **Stream = `(aggregate_type, aggregate_id)`.** Cada aggregate se reconstruye reproduciendo
  (replay) los eventos de su propio stream en orden de `sequence_number` — nunca se lee el
  stream de otro aggregate para reconstruir el estado actual.
- **Escritura:** cada Use Case ejecuta dentro de una Unit of Work (`ADR-009`) que hace `append`
  de exactamente los eventos que produce esa invocación (uno en los comandos de este modelo,
  salvo `EvaluacionIniciada` que además persiste el read model de `PreguntaAsignada` en la misma
  transacción) — commit atómico, rollback automático ante cualquier excepción de dominio.
- **Concurrencia optimista:** `sequence_number` esperado se valida al escribir (evita que un
  doble submit del estudiante — ej. reconexión con reintento de red — duplique una `Respuesta`
  con `RespuestaRegistrada`).
- **Read models (CQRS), actualizados síncronamente en la misma transacción del evento** (a esta
  escala — 30 a 60 alumnos — no se justifica la complejidad de proyección asíncrona):
  - `evaluaciones_activas_por_actividad` — `(evaluacion_id, actividad_id, estado, ultima_actividad_en)`
    para toda `Evaluacion` que no esté `Finalizada`. Sostiene INV-AE-04 (RF-11b) y las dos
    queries del `VerificadorDeVencimientos` (§6b). `ultima_actividad_en` se actualiza con cada
    `RespuestaRegistrada` y `EvaluacionReanudada`.
  - `evaluacion_detalle` — sostiene la query de revisión (RF-13), incluida la comparación contra
    la respuesta correcta.
- **Frontera con Analytics:** Analytics (BC separado, RF-15 a RF-17, fuera de este incremento)
  consume este mismo event store en modo solo-lectura vía puerto — no se diseña en este
  documento, pero el event store queda preparado para eso desde el inicio (`ADR-002`).

---

## 6b. Disparo automático por tiempo — `VerificadorDeVencimientos`

Componente que faltaba explicitar: **no es un aggregate** (no tiene invariantes de dominio
propias ni stream de eventos) — es una **Policy/Process Manager** que reacciona al paso del
tiempo, no a un comando de un actor humano. Es el mecanismo concreto detrás de los dos puntos
que quedaban solo mencionados como "Sistema" en §3/§8 antes de esta revisión.

**Disparador:** ejecución periódica (job en background — cadencia a definir en la spec de
implementación de la Iteración 2, ej. cada 1–5 minutos; a esta escala de 30-60 alumnos no
justifica un mecanismo más fino que polling). Alternativa de menor infraestructura, válida como
mismo criterio: chequeo perezoso disparado por cualquier query relevante (ej. al listar
evaluaciones activas), aceptando una demora acotada entre el vencimiento real y la emisión del
evento — no es un caso donde la exactitud al segundo importe (a diferencia del ranking en vivo,
`RNF_v1.md` Escenario 1, que si tiene ese requisito y no aplica a este BC).

**Regla 1 — inactividad (nuevo, a pedido de Víctor):**
```
Para cada Evaluacion en evaluaciones_activas_por_actividad con estado = EnCurso:
  si (ahora - ultima_actividad_en) > UMBRAL_INACTIVIDAD:
    emitir SuspenderEvaluacion(evaluacion_id)   -- actor: Sistema
```
`UMBRAL_INACTIVIDAD` es un parámetro de configuración (no invariante de dominio) — valor
concreto pendiente, ver §8. La ejecución repetida de esta regla sobre la misma `Evaluacion` ya
`Suspendida` no reemite el evento: `SuspenderEvaluacion` disparado por la Policy sobre una
`Evaluacion` ya `Suspendida` es un no-op silencioso, a diferencia del pedido manual del
estudiante sobre una ya suspendida, que sí puede recibir `EvaluacionYaSuspendida` como feedback
de UI (mismo comando, la excepción se trata distinto según si el emisor es la Policy o un
actor humano).

**Regla 2 — vencimiento del período, pasivo (ya existía como hot spot §8.1, ahora con mecanismo
explícito):**
```
Para cada ActividadEvaluativaPeriodoAbierto con fecha_cierre < ahora y cerrada_manualmente = false:
  para cada Evaluacion en evaluaciones_activas_por_actividad de esa actividad
      (estado = EnCurso o Suspendida):
    emitir FinalizarEvaluacion(evaluacion_id)   -- actor: Sistema
```
Corre después de cualquier `ModificarPeriodoDisponibilidad` que extienda el plazo — una
actividad extendida a tiempo dentro de esta misma pasada del job nunca llega a finalizar
evaluaciones que en realidad siguen vigentes (la regla lee `fecha_cierre` vigente en el momento
de la ejecución, no un valor cacheado).

**Regla 3 — cierre manual del docente (`CerrarActividad`, §3/§4/§5): cascada síncrona, no vía
Policy.** A diferencia de las Reglas 1 y 2, esta no espera la próxima pasada del job — el
docente quiere terminar la actividad ahora (ej. "la clase ya terminó"), no dentro de 1–5
minutos. El propio Use Case de `CerrarActividad`, en la misma Unit of Work que emite
`ActividadEvaluativaCerrada` (`ADR-009`), consulta `evaluaciones_activas_por_actividad` para esa
actividad y emite `FinalizarEvaluacion(evaluacion_id)` para cada una — mismo efecto que la
Regla 2, disparado de forma inmediata y no periódica. La Regla 2 queda igual acotada a
`cerrada_manualmente = false` (arriba) para no pisar ni duplicar este camino.

**Idempotencia:** las tres reglas son seguras de re-ejecutar — si el job corre dos veces sobre
el mismo estado (ej. quedó a mitad de una pasada), el segundo intento sobre una `Evaluacion` que
ya cambió de estado por una pasada anterior (o por la cascada síncrona de la Regla 3) no tiene
efecto (los invariantes INV-AE-11/INV-AE-12 del propio aggregate `Evaluacion` lo protegen — el
Use Case que ejecuta cada comando emitido por la Policy sigue las mismas reglas que si lo
llamara un actor humano).

**Nota de implementación (`US-3.2.4`, confirmada con Víctor 2026-08-27) — dos decisiones que se
apartan de lo escrito arriba, documentadas en `docs/specs/inc3/US-3.2.4.md`:**
1. `evaluaciones_activas_por_actividad` **no** se implementó como tabla sincronizada en cada
   evento — se implementó como una query de lectura sobre la tabla `events` existente
   (`EvaluacionActivaQueryPort`/`SQLAlchemyEvaluacionActivaQueryRepository`), para no tocar los
   4 Use Case ya cerrados de `US-3.1.3` a `US-3.2.3` ni sumar una migración nueva. A esta escala
   el propio párrafo de arriba ya admite que "no justifica un mecanismo más fino que polling" —
   mismo criterio aplicado acá.
2. El disparador es un `asyncio.create_task` en el `lifespan` de `src/app.py` (cadencia 120s),
   no un job externo — el proyecto no tiene APScheduler/Celery.

Las Reglas 1, 2 y 3 (`SuspenderEvaluacion`/`FinalizarEvaluacion` con `actor="sistema"`, y la
cascada síncrona de `CerrarActividad`) están implementadas tal como se describen arriba —
Regla 3 en `US-3.3.2` (`CerrarActividadUseCase`), sin diferencias respecto de lo modelado.

---

## 7. Integraciones con otros BC (vía puertos, sin imports directos)

Mismo patrón que `MateriaPort` (BC Identidad → BC Banco de Preguntas, `US-2.1.2`) — cada puerto
se define y consume dentro de `src/actividad_evaluativa/entities/ports/`, implementado por un
adapter in-process propio en `src/actividad_evaluativa/frameworks/adapters/`:

| Puerto (a definir) | Consumido por | Resuelve |
|---|---|---|
| `PreguntaConsultaPort` → BC Banco de Preguntas (`PreguntaRepositoryPort.filtrar`/`obtener_por_id`) | `CrearActividadPeriodoAbierto` (INV-AE-01), `IniciarEvaluacion` (arma el set aleatorio, RF-12), `RegistrarRespuesta` (INV-AE-10) | Contar preguntas activas de la materia, samplear `cantidad_preguntas` al azar, consultar la respuesta correcta vigente |
| `MateriaConsultaPort` → BC Banco de Preguntas | `CrearActividadPeriodoAbierto` | Validar que `materia_id` existe |
| `EstudianteConsultaPort` → BC Identidad | `IniciarEvaluacion` | Validar que `estudiante_id` existe y tiene rol Estudiante |

El sampleo aleatorio de RF-12 se resuelve en el propio Use Case de `IniciarEvaluacion`
(`random.sample` sobre el resultado de `PreguntaConsultaPort`) — no requiere ensanchar el puerto
de Banco de Preguntas con un método de muestreo aleatorio, mismo criterio de "no ensanchar
puertos existentes" ya aplicado en `US-2.1.9`.

---

## 8. Hot spots — resueltos con Víctor (2026-08-25)

Estos puntos no estaban cubiertos literalmente por el texto de RF-11/RF-11b:

1. **¿`FinalizarEvaluacion` es siempre una acción explícita del estudiante, o el sistema
   finaliza automáticamente las evaluaciones que siguen `EnCurso`/`Suspendida` cuando
   `fecha_cierre` pasa?** Resuelto — ambas: el estudiante puede finalizar antes de responder
   todo, y el sistema finaliza automáticamente lo que quedó activo al llegar `fecha_cierre`
   (para que RF-13 quede disponible sin depender de que el estudiante vuelva a entrar).
   Mecanismo explícito: `VerificadorDeVencimientos`, Regla 2 (§6b).
2. **¿`ModificarPeriodoDisponibilidad` se permite después de que `fecha_cierre` ya pasó** (no
   solo "mientras está activa")? Resuelto — sí, en cualquier momento, **mientras la actividad no
   haya sido cerrada manualmente** (matiz agregado en el punto 5): no hay un estado "cerrada
   definitivamente" por el solo paso del tiempo que lo bloquee — cubre el escenario de RF-11b
   donde la caída del sistema duró hasta después del horario de cierre original. La única forma
   de llegar a un estado terminal que sí lo bloquea es la decisión deliberada del docente
   (`CerrarActividad`, INV-AE-04b).
3. **Nomenclatura:** este documento usa `Evaluacion` como término nuevo del lenguaje ubicuo
   (§2) — falta incorporarlo a `docs/architecture/03-bounded-contexts.md` §Actividad Evaluativa
   cuando se apruebe. `Respuesta` y `PreguntaAsignada` ya estaban en ese lenguaje ubicuo desde
   antes de este modelado — no se agregan, solo se les da estructura concreta (§5, punto 6).

4. **Suspensión de `Evaluacion` — manual y automática por inactividad (agregado a pedido de
   Víctor, ronda de revisión posterior a la primera aprobación pendiente):** el modelo original
   no tenía estado intermedio entre `EnCurso` y `Finalizada`. Se agrega `Suspendida` (§5),
   comandos `SuspenderEvaluacion`/`ReanudarEvaluacion` (§3, §4), invariantes INV-AE-11/12, y el
   mecanismo explícito que detecta la inactividad y dispara la suspensión automática:
   `VerificadorDeVencimientos`, Regla 1 (§6b) — mismo componente que ya resolvía el punto 1.
5. **Cierre manual de la actividad por el docente, como medida opcional (agregado a pedido de
   Víctor, tercera ronda de revisión):** comando `CerrarActividad` (§3/§4), evento
   `ActividadEvaluativaCerrada` — nombre ya establecido por `ADR-015` para el renombre de
   `SesionCerrada`, ahora sí modelado con su comando y sus invariantes. Resuelto: (a) finaliza en
   cascada las `Evaluacion` activas de inmediato, no espera la próxima pasada del
   `VerificadorDeVencimientos` (Regla 3, §6b); (b) es terminal — no admite reabrir con
   `ModificarPeriodoDisponibilidad` (INV-AE-04b), a diferencia de la expiración pasiva de
   `fecha_cierre` (punto 2).
6. **`Respuesta` es Entity, no Value Object (corrección a pedido de Víctor, cuarta ronda de
   revisión):** una versión previa de este documento anidaba "intentos" como Value Objects
   anónimos dentro de `PreguntaAsignada`. Corregido: `Respuesta` (término ya existente en el
   lenguaje ubicuo, punto 3) es una Entity con `id` propio — cada confirmación de una respuesta
   es un hecho único e irrepetible, no un valor transitorio dentro de otra estructura. Vive como
   colección de primer nivel `respuestas` directamente en `Evaluacion` (§5), no anidada bajo
   `PreguntaAsignada`. Efecto en cascada de este cambio: comando `RegistrarIntentoRespuesta`
   renombrado a `RegistrarRespuesta`, evento `IntentoRespuestaRegistrado` renombrado a
   `RespuestaRegistrada` — este último ya era el nombre fijado por `ADR-015` (columna "sin
   cambio" de su tabla de renombres), que la versión previa de este documento no había
   respetado.

**Pendiente de definir en la spec de implementación (no bloquea la aprobación del modelo):**
- **Duración del período de inactividad** (`UMBRAL_INACTIVIDAD`, §6b) que dispara
  `SuspenderEvaluacion` automático — ej. 15/30 minutos sin `RespuestaRegistrada` ni
  `EvaluacionReanudada`. Parámetro de configuración, no invariante de dominio.
- **Cadencia del job** del `VerificadorDeVencimientos` (§6b) — ej. cada 1–5 minutos, o chequeo
  perezoso al consultar.
- `ReanudarEvaluacion` es explícito (decisión ya tomada arriba) — la UX de US-3.0.2 debe cubrir
  la pantalla/estado de "evaluación suspendida, tocá para continuar" tanto para suspensión
  manual como automática.

---

## 9. Próximo paso

Modelo completo, sin hot spots abiertos (§8) — pasa a aprobación explícita de Víctor en el
comentario de cierre del Issue #137 (DoD tipo `Modelado`, `WORKFLOW-DESARROLLO.md` §2). Una vez
aprobado, es el input de las specs US-IEDD de las Iteraciones 1 a 3
(`docs/plans/inc3/inc3-candidatas.md`) y del prototipo UX de US-3.0.2 (Issue #138).
