# BC Actividad Evaluativa — Wireframes: Sesión de Período Abierto

> Estado documental: **vigente — aprobado por Víctor (2026-08-26, sesión de modelado de la
> Iteración 0 del Incremento 3).**
> Alcance: exclusivamente el modo **período abierto** (RF-11, RF-11b, RF-12, RF-13). El modo
> **en vivo** (RF-08 a RF-10) no forma parte de este documento.
>
> Fuente: `docs/rf/RF_v1.md` (RF-11, RF-11b, RF-12, RF-13), `docs/rf/RNF_v1.md` (Confiabilidad —
> escenario de interrupción durante sesión de período abierto; Usabilidad, escenario 1 —
> PC/tablet/smartphone), `docs/design/domain/BC-actividad-evaluativa-modelo.md` (comandos,
> eventos, invariantes INV-AE-01 a 12, §8 hot spots resueltos con Víctor).
>
> Prototipo: `docs/design/ux/prototipos/actividad-evaluativa-periodo-abierto.html` — navegable,
> 12 pantallas.

---

## 1. Identidad visual

Misma paleta y tipografía que `wireframes-banco-preguntas.md` §1 y
`wireframes-cuentas-administracion.md` §1 (azul institucional `#1D75B5`, verde de acento
`#53AA74`, Roboto) — continuidad visual entre BCs e iteraciones, sin redefinir tokens nuevos.
Primitivas reutilizadas de `US-ADJ-01`: `Card` (listado de actividades), `Badge` (estado de
actividad/evaluación), `Breadcrumb`. Primitivas **nuevas** de este BC, sin precedente en
Identidad/Banco de Preguntas: barra de progreso (`.progress-bar`), tarjeta de pregunta
(`.question-card`), indicador de preguntas por punto (`.exam-nav .dot`), tarjeta de revisión
por pregunta (`.review-item`), barra de resumen de resultado (`.summary-bar`).

---

## 2. Pantallas — Docente

### 2.0 Mis materias (`#doc-materias`)

**Actor:** Docente.
**Query:** materias donde el docente está asignado (mismo dato que `Materias.tsx` del Banco de
Preguntas, `US-2.1.9` — no se especifica acá si la implementación reutiliza esa misma pantalla
o levanta una nueva en `src/actividad_evaluativa/`, es decisión de la spec de implementación de
Iteración 1; a nivel UX es el mismo punto de entrada).

| Elemento | Detalle |
|---|---|
| Contexto | Breadcrumb "Actividad evaluativa › Mis materias" — entry point del BC, sin materia todavía seleccionada |
| Tarjetas | Una por materia asignada al docente: nombre, comisión, cantidad de actividades en curso |
| Navegación | Cada tarjeta abre el listado de actividades de esa materia (`#doc-actividades`) |
| Agregado a pedido de Víctor | Sin esta pantalla, "Actividades" asumía una materia fija en el contexto de navegación — con más de una materia asignada (caso real: Ingeniería de Software + Gestión de Proyectos) hacía falta el nivel de selección previo, mismo patrón ya usado en Banco de Preguntas |

### 2.1 Listado de actividades (`#doc-actividades`)

**Actor:** Docente.
**Query:** listado de `ActividadEvaluativaPeriodoAbierto` de una materia.

| Elemento | Detalle |
|---|---|
| Contexto | Breadcrumb "Mis materias › {Materia} › Actividades" |
| Tarjetas | Una por actividad: título, ventana de apertura/cierre, `Badge` de estado (`En curso` / `Programada` / `Cerrada`), cantidad de evaluaciones activas o finalizadas |
| Acción | "+ Nueva actividad" |
| Estado del `Badge` | `En curso` = dentro del período y no cerrada manualmente; `Programada` = `fecha_apertura` futura; `Cerrada` = `cerrada_manualmente = true` **o** `fecha_cierre` ya pasada |
| Navegación | Cada tarjeta abre el detalle (`#doc-detalle-actividad`) |

### 2.2 Nueva actividad (`#doc-nueva-actividad`)

**Actor:** Docente.
**Comando:** `CrearActividadPeriodoAbierto(materia_id, fecha_apertura, fecha_cierre, cantidad_preguntas, cantidad_intentos_permitidos)`.

| Elemento | Detalle |
|---|---|
| Campos | Apertura (fecha/hora), Cierre (fecha/hora), Cantidad de preguntas, Intentos permitidos por pregunta (default 1) |
| Validación de cliente | `fecha_apertura` < `fecha_cierre` (INV-AE-02, espejo del lado servidor); intentos ≥ 1 (INV-AE-03) |
| Hint | Aclara que `cantidad_preguntas` no puede superar las preguntas activas del banco de la materia (INV-AE-01) — el número exacto disponible se muestra como referencia, la validación dura la hace el backend |
| Hint | Aclara el sampleo aleatorio: cada estudiante recibe un set distinto (RF-12) |
| Materia | Implícita por el contexto de navegación (mismo patrón que "Nueva pregunta" en Banco de Preguntas) — no es un campo editable en este formulario |
| Acciones | "Crear actividad" / "Cancelar" |
| Error server-side (fuera del prototipo, a especificar en la US de implementación) | 422 con `PreguntasInsuficientes`, `PeriodoInvalido`, `CantidadIntentosInvalida`, `MateriaNoExiste` |

### 2.3 Detalle de actividad (`#doc-detalle-actividad`)

**Actor:** Docente.

| Elemento | Detalle |
|---|---|
| Datos | Apertura, cierre, cantidad de preguntas, intentos permitidos, evaluaciones activas (en curso o suspendidas), evaluaciones finalizadas |
| Acción "Extender plazo" | Siempre visible mientras la actividad no esté cerrada manualmente (INV-AE-04b) — va a `#doc-extender-plazo` |
| Acción "Cerrar actividad ahora" | Destructiva, opcional (§3 del modelo — "medida opcional del docente, no un paso obligatorio") — va a `#doc-cerrar-actividad` |
| Hint | Aclara que "Extender plazo" solo mueve el cierre hacia adelante sin restricción; acortarlo exige cero evaluaciones activas (INV-AE-04, RF-11b caso límite) |
| Fuera de alcance | Listado nominal de estudiantes/evaluaciones — RF-11/RF-11b no lo piden; el conteo agregado alcanza para esta iteración (mismo criterio de "no ensanchar el alcance de la spec" ya aplicado en Banco de Preguntas) |

### 2.4 Extender plazo (`#doc-extender-plazo`)

**Actor:** Docente.
**Comando:** `ModificarPeriodoDisponibilidad(actividad_id, nueva_fecha_cierre)`.

| Elemento | Detalle |
|---|---|
| Aviso | Alerta de advertencia: efecto inmediato, aplica a los estudiantes con evaluaciones activas |
| Campos | Cierre actual (solo lectura), nuevo cierre |
| Hint | Si el docente intenta acortar con evaluaciones activas, el mensaje de error (`NoSePuedeAcortarConEvaluacionesActivas`) se muestra inline en el campo — no cubierto como pantalla separada en el prototipo, mismo criterio que los 422 de validación en otros formularios del proyecto (ej. `NuevaMateria.tsx`) |
| Acciones | "Guardar nuevo cierre" / "Cancelar" (vuelve al detalle) |

### 2.5 Cerrar actividad (`#doc-cerrar-actividad`)

**Actor:** Docente.
**Comando:** `CerrarActividad(actividad_id)`.

| Elemento | Detalle |
|---|---|
| Alerta destructiva | Explica la cascada: finaliza de inmediato las evaluaciones activas tal como están respondidas, es terminal (INV-AE-04b — no se puede reabrir ni extender después) |
| Contexto | Aclara cuándo usarlo: solo si la actividad terminó su propósito antes de lo previsto — la mayoría de las actividades no lo necesita |
| Acciones | "Sí, cerrar actividad ahora" (destructiva) / "Cancelar" |

---

## 3. Pantallas — Estudiante

### 3.0 Mis materias (`#est-materias`)

**Actor:** Estudiante.
**Query:** materias de la comisión del estudiante.

| Elemento | Detalle |
|---|---|
| Contexto | Breadcrumb "Actividad evaluativa › Mis materias" — entry point del BC del lado estudiante |
| Tarjetas | Una por materia de su comisión: nombre, comisión, `Badge` resumen ("N pendiente" / "Sin actividades disponibles") |
| Navegación | Cada tarjeta abre el listado de actividades de esa materia (`#est-actividades`) |
| Agregado a pedido de Víctor | Mismo motivo que `#doc-materias` (§2.0) — un estudiante cursa más de una materia (Ingeniería de Software + Gestión de Proyectos), necesita elegir antes de ver actividades |

### 3.1 Listado de actividades (`#est-actividades`)

**Actor:** Estudiante.

| Elemento | Detalle |
|---|---|
| Contexto | Breadcrumb "Mis materias › {Materia} › Actividades" |
| Tarjetas | Una por actividad visible para su comisión: título, ventana, `Badge` de estado desde la perspectiva del estudiante |
| Estados del `Badge` | `Pendiente de responder` (dentro del período, sin `Evaluacion` finalizada) · `Todavía no abrió` (antes de `fecha_apertura`) · `Finalizada — ver revisión` (el estudiante ya finalizó su `Evaluacion`) |
| Navegación | `Pendiente de responder` → `#est-rendir` (o `#est-suspendida` si ya existe una `Evaluacion` `Suspendida`, ver INV-AE-11); `Todavía no abrió` → `#est-fuera-periodo`; `Finalizada` → `#est-revision` |
| Fuera de alcance | No se distingue visualmente `EnCurso` de `Suspendida` en esta grilla — ambas caen en "Pendiente de responder"; la distinción ocurre recién al entrar (`IniciarEvaluacion` es idempotente, retoma sin diferenciar el origen) |

### 3.2 Fuera de período (`#est-fuera-periodo`)

**Actor:** Estudiante.
**Precondición:** intento de `IniciarEvaluacion` fuera de la ventana vigente → `FueraDePeriodo`.

| Elemento | Detalle |
|---|---|
| Mensaje | Un único estado visual cubre los dos casos que pide el criterio de aceptación de `US-3.0.2` (antes de apertura, después de cierre) — mismo criterio que `US-1.1.3` (mensaje genérico sin distinguir motivo al estudiante) |
| Caso "antes de apertura" | Muestra la fecha/hora exacta de apertura |
| Caso "después de cierre, nunca iniciada" | Mismo layout — nota aclaratoria al pie distingue el caso sin necesitar una pantalla separada (ver nota en el prototipo) |
| Diferencia con `#est-revision` | Si el estudiante **ya** tiene una `Evaluacion` `Finalizada` para esa actividad (por vencimiento automático, `VerificadorDeVencimientos` Regla 2, o porque la finalizó él mismo), no cae acá — va directo a la revisión (RF-13 sigue disponible aunque el período ya cerró) |

### 3.3 Rendir evaluación (`#est-rendir`)

**Actor:** Estudiante.
**Comando por confirmación:** `RegistrarRespuesta(evaluacion_id, pregunta_id, respuesta)`.

| Elemento | Detalle |
|---|---|
| Progreso | Barra + contador "Pregunta N de {cantidad_preguntas}" + cantidad ya respondida + fecha de cierre vigente |
| Pregunta actual | Card con el enunciado y las opciones — mismo componente visual de opción que `NuevaPreguntaOpcionMultiple.tsx` (radio, resaltado al seleccionar), reutilizado como lector, no editor |
| Navegación entre preguntas | Puntos numerados (`.dot`) — verde = respondida, azul = actual, gris = pendiente; "Anterior"/"Confirmar y siguiente" |
| Hint de confiabilidad | Aclara explícitamente que cada respuesta se guarda al confirmarla (INV-AE-09, persistencia atómica) — es la pieza de UX que sostiene el escenario RNF de "reconexión sin pérdida" pedido por el criterio de aceptación de `US-3.0.2`: no hay una pantalla de "error de conexión" separada porque el modelo ya garantiza que lo confirmado quedó guardado; al volver a entrar, `IniciarEvaluacion` retoma la `Evaluacion` en el mismo punto |
| "Pausar y salir" | Header — dispara `SuspenderEvaluacion` manual, va a `#est-suspendida` |
| Sin feedback de corrección | Ninguna opción muestra si es correcta al responder (hot spot resuelto del modelo, §5) — solo se sabe al finalizar (RF-13) |
| Preguntas ya con intentos agotados | Si `cantidad_intentos_permitidos` > 1 y se agotó, la pregunta se muestra sin opción de reenviar — detalle de estado a definir en la spec de implementación, no bloquea la aprobación de este wireframe |

### 3.4 Evaluación suspendida (`#est-suspendida`)

**Actor:** Estudiante (o disparado automáticamente por `VerificadorDeVencimientos`, Regla 1 — inactividad).
**Comando:** `ReanudarEvaluacion(evaluacion_id)` al continuar.

| Elemento | Detalle |
|---|---|
| Mensaje | Confirma cuántas respuestas ya quedaron guardadas, sin distinguir si la suspensión fue manual o automática — mismo hecho de dominio para el estudiante (`BC-actividad-evaluativa-modelo.md` §3, nota "es el mismo hecho de dominio sin importar quién lo disparó") |
| Acción única | "Continuar" → `#est-rendir`, retoma en la pregunta donde quedó (INV-AE-05, el set no cambia) |
| Alerta informativa | Explica el mecanismo automático de inactividad, para que no sorprenda si el estudiante nunca tocó "Pausar y salir" explícitamente |
| Cubre el pendiente del modelo | Este es el estado "evaluación suspendida, tocá para continuar" que `BC-actividad-evaluativa-modelo.md` §8 dejaba explícitamente a cargo de `US-3.0.2` |

### 3.5 Revisión al finalizar (`#est-revision`)

**Actor:** Estudiante.
**Query:** `ObtenerRevisionEvaluacion(evaluacion_id)`.

| Elemento | Detalle |
|---|---|
| Resumen | Barra con correctas/incorrectas/total |
| Detalle por pregunta | Enunciado, `Badge` correcta/incorrecta, la respuesta propia, y — solo si falló — la respuesta correcta (RF-13, criterio de aceptación exacto) |
| Disponibilidad | Visible únicamente tras `EvaluacionFinalizada` — nunca antes (RF-13: "el detalle completo es visible inmediatamente al finalizar, no antes") |
| Acceso | Desde el listado (`#est-actividades`, tarjeta en estado `Finalizada`) — sin límite de tiempo posterior explícito en RF-13, se asume que la revisión queda disponible indefinidamente (mismo criterio que un historial, a confirmar en la spec de implementación si Víctor quiere acotarlo) |

---

## 4. Matriz RF → pantalla

| RF | Pantallas |
|---|---|
| RF-11 (creación) | `#doc-nueva-actividad` |
| RF-11b (modificación de período, caso límite de acortar) | `#doc-extender-plazo`, hint de restricción |
| RF-12 (set aleatorio) | Hint en `#doc-nueva-actividad`; consumido implícitamente en `#est-rendir` |
| RF-13 (revisión) | `#est-revision` |
| Estado fuera de período (criterio de aceptación de `US-3.0.2`, no un RF propio) | `#est-fuera-periodo` |
| Suspensión (hot spot del modelo, §8, pendiente explícito para este documento) | `#est-suspendida` |
| Cierre manual (`CerrarActividad`, opcional, no un RF propio — parte del modelo aprobado en `US-3.0.1`) | `#doc-cerrar-actividad` |

---

## 5. Fuera de alcance de este wireframe

- Modo en vivo (RF-08 a RF-10) — BC/incremento separado.
- Notificaciones de apertura/cierre por email (RF-14) — Incremento 5.
- Portal de desempeño histórico del estudiante (RF-15) — Incremento 4.
- Listado nominal de estudiantes por actividad, con su estado individual — no lo pide RF-11/RF-11b; el conteo agregado en `#doc-detalle-actividad` alcanza.
- Configuración del `UMBRAL_INACTIVIDAD` y la cadencia del `VerificadorDeVencimientos` — parámetros de infraestructura, no de UX (`BC-actividad-evaluativa-modelo.md` §8, "pendiente de definir en la spec de implementación").
