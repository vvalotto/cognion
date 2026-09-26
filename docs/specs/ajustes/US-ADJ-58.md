# US-ADJ-58: Cancelar una sesión en vivo no iniciada, y no iniciar sin participantes (regla de dominio)

**Estado**: `Especificada`
**Iteracion / Sprint**: sin asignar — a decidir con Víctor (antes o después del cierre de `BL-011`)
**Tipo**: `feat` backend + frontend
**Agregado principal afectado**: `ActividadEvaluativaEnVivo`
**Bounded Context**: Actividad Evaluativa
**Origen**: revisión manual de la app (2026-09-26), hallazgo #4 (`quality/reports/uat/inc6/revision-manual-app.md`).

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **cancelar una sesión en vivo que creé y no voy a dar**,
para **que deje de figurar como activa y los estudiantes no se queden esperando en la sala**.

Y quiero que **una sesión no pueda iniciarse sin estudiantes unidos**, como regla del sistema y no solo de la pantalla.

---

## Contexto del dominio

### Problema

1. **No se puede cancelar.** Una sesión creada y nunca iniciada queda `EnEspera` para siempre: sigue en "Sesiones
   en vivo activas" del Docente y en la pantalla de actividades del Estudiante. `FinalizarSesionEnVivo` exige
   `EnCurso` y la pregunta cerrada (INV-AEV-03), así que no sirve para descartarla. El único camino hoy es
   iniciarla y finalizarla "de mentira".
2. **Iniciar sin participantes.** En la revisión se decidió que no tiene sentido iniciar sin nadie unido (reemplaza
   el "podés iniciar igual" de `US-6.3.0` H9). El frontend ya deshabilita el botón (hallazgo #4), pero el dominio lo
   permite a propósito (`ActividadEvaluativaEnVivo.iniciar()`: "no exige participantes", `US-6.1.4`): la API sigue
   aceptándolo.

**Ya resuelto en frontend (fuera de esta US):** "Iniciar sesión" deshabilitado con 0 participantes y "‹ Salir" en la
sala y la proyección (salir no toca la sesión; se retoma con "Continuar").

### Modelo involucrado (propuesta, se confirma en la Fase 2)

| Elemento | Detalle |
|---|---|
| Comando nuevo | `CancelarSesionEnVivo(sesion_id)` — Docente |
| Evento nuevo | `SesionEnVivoCancelada` (payload mínimo: `sesion_id`, `ocurrido_en`) |
| Estado | `Cancelada` como nuevo valor de `EstadoSesionEnVivo` (terminal, como `Finalizada`) — o reutilizar `Finalizada` con marca; se decide en la Fase 2. Propuesta: estado propio, para que Analytics (`US-ADJ-56`) no la cuente como sesión jugada |
| Invariante nuevo | **INV-AEV-10:** `CancelarSesionEnVivo` solo en `EnEspera` (una sesión iniciada se termina con `FinalizarSesionEnVivo`) |
| Invariante nuevo | **INV-AEV-11:** `IniciarSesionEnVivo` requiere al menos una `ParticipacionEnVivo` (`SinParticipantes`, `422`) |
| Endpoint | `POST /sesiones-en-vivo/{id}/cancelar` (rol `docente`) |
| Canal | Broadcast `sesion_cancelada` a los conectados (Estudiantes en la sala) |
| Listados | Una sesión `Cancelada` no aparece en "Sesiones en vivo activas" ni en las tarjetas del Estudiante |
| Frontend | Botón "Cancelar sesión" en la sala del Docente, con confirmación; el Estudiante en la sala ve "El Docente canceló la sesión" y vuelve a sus actividades |

---

## Especificacion del comportamiento

### Precondicion

- `US-6.3.10` cerrada.

### Postcondicion

- El Docente cancela una sesión no iniciada; deja de figurar como activa para todos.
- La API rechaza iniciar una sesión sin participantes.
- `BC-actividad-evaluativa-modelo.md` (§§10-18) documenta el comando, el evento, el estado y los dos invariantes.
- Circuitos E2E (`frontend/e2e/`) ampliados con la cancelación.

---

## Criterios de aceptacion

```gherkin
Feature: Cancelar una sesión en vivo y no iniciar sin participantes (US-ADJ-58)

  Scenario: Cancelar una sesión en espera
    Given una sesión en vivo EnEspera
    When el Docente la cancela y confirma
    Then la sesión queda Cancelada y deja de figurar en "Sesiones en vivo activas"

  Scenario: Los estudiantes en la sala se enteran
    Given dos Estudiantes esperando en la sala
    When el Docente cancela la sesión
    Then ven "El Docente canceló la sesión" y pueden volver a sus actividades

  Scenario: La tarjeta desaparece para el Estudiante
    Given una sesión cancelada
    When el Estudiante abre las actividades de su materia
    Then la sesión no aparece

  Scenario: No se cancela una sesión iniciada
    Given una sesión EnCurso
    When se intenta cancelarla
    Then se rechaza con 422 y la sesión sigue EnCurso

  Scenario: No se inicia sin participantes
    Given una sesión EnEspera sin estudiantes unidos
    When se intenta iniciarla por la API
    Then se rechaza con 422 SinParticipantes

  Scenario: Con un participante se inicia
    Given una sesión EnEspera con un estudiante unido
    When el Docente la inicia
    Then pasa a EnCurso

  Scenario: Cancelar dos veces
    Given una sesión ya cancelada
    When se intenta cancelarla de nuevo
    Then se rechaza con 422 y no se emite otro evento
```

---

## Impacto arquitectonico

- [x] Sí — comando, evento, estado e invariantes nuevos en `ActividadEvaluativaEnVivo`; endpoint y mensaje de canal
  nuevos. Vigilar el **CBO** de `ConduccionEnVivoController` (4 use cases hoy): evaluar un controller propio.

---

## Decisiones abiertas (para la Fase 2, con Víctor)

1. Estado propio `Cancelada` vs. reutilizar `Finalizada`. Propuesta: **propio**.
2. ¿Se puede cancelar una sesión `EnCurso` (por ejemplo, con 0 respuestas)? Propuesta: **no**, se usa Finalizar.
3. ¿Se notifica por email a los estudiantes de la Comisión (Notificaciones, `RF-14`)? Propuesta: **no**, solo el canal.

---

## Fuente de verdad UX

- `docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md` — **a ampliar** (gate UX) con el botón "Cancelar
  sesión" y su confirmación en `#doc-sala-espera`, y el mensaje de sesión cancelada en `#est-sala-espera`. Actualizar
  H9 con la regla de no iniciar sin participantes.

---

## Referencias

- Modelo: `BC-actividad-evaluativa-modelo.md` §§10-18; `US-6.1.4` (iniciar), `US-6.2.7` (finalizar)
- Origen: revisión manual, hallazgo #4
