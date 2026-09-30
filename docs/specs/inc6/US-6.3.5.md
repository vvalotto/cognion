# US-6.3.5: Docente crea la sesión en vivo desde una Comisión y abre la sala de espera

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-6.3`
**Tipo**: `feat frontend`
**Agregado principal afectado**: — (consume `CrearSesionEnVivo` e `IniciarSesionEnVivo`)
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **crear una sesión en vivo desde el detalle de mi Comisión y ver quién se va uniendo**,
para **empezar la dinámica cuando la clase esté lista**.

---

## Contexto del dominio

### Problema

Es la puerta de entrada del Docente al modo en vivo. La sesión se crea **desde una Comisión puntual**
(`comision_id` única y obligatoria, sexta ronda de `US-6.0.2`): no existe "todas las Comisiones". Cubre
`§2.1 #doc-nueva-sesion` y `§2.2 #doc-sala-espera` de los wireframes aprobados, más el bloque de **sesiones
activas** de `US-6.3.0` (H6), sin el cual una sesión creada no se puede recuperar.

### Pantallas

| Pantalla | Ruta | Comportamiento |
|---|---|---|
| **Punto de entrada** (existente) | `ComisionDetalleDocente.tsx` (`US-ADJ-26`) | Botón **"+ Nueva sesión en vivo"** y bloque **"Sesiones en vivo activas"** (`listarSesionesEnVivo`, `US-6.3.2`): cada sesión con su `Badge` y "Continuar" → sala si `EnEspera`, proyección si `EnCurso` |
| **Nueva sesión** | `/sesiones-en-vivo/comisiones/:comisionId/nueva` | Formulario de `§2.1` |
| **Sala de espera** | `/sesiones-en-vivo/:sesionId/sala` | Chips de participantes en vivo, datos de la sesión, "Iniciar sesión" |

### Formulario (§2.1)

- Campos: Unidad temática (opcional), Tema (opcional), Cantidad de preguntas, Tiempo límite por pregunta en segundos
  — **sin valor por defecto** (spike RF-10, confirmado con Víctor). **Sin selector de Comisión.**
- Unidad temática / Tema: `<datalist>` con las del banco de la Materia (mismo patrón que `US-ADJ-02`, `NuevaActividad`).
- Validación de cliente: cantidad ≥ 1, tiempo límite > 0 (espejo de INV-AEV-02).
- Breadcrumb "Actividad evaluativa › {Materia} › {Comisión} › Nueva sesión en vivo"; la Materia y la Comisión se
  resuelven por la ruta (`comisionId` → `GET /comisiones/{id}`, ya existente) y `listarMaterias`.
- Hint: el puntaje combina velocidad, dificultad e importancia.
- Errores del servidor mostrados con su `detail`: `ComisionNoExiste` (404), `PreguntasInsuficientes` (INV-AEV-01, 422),
  `TiempoLimiteInvalido` (INV-AEV-02, 422).
- Éxito → navega a la sala.

### Sala de espera (§2.2)

- Datos: cantidad de preguntas, Materia, tiempo límite por pregunta.
- **Participantes:** carga inicial con `GET .../participantes` (`US-6.3.1`, con nombre) y luego en vivo con
  `participantes_actualizados` por el canal (`US-6.3.4`) — sin recargar. Reemplaza la lista completa en cada mensaje
  (el mensaje trae la lista, no un delta).
- Hint: se puede seguir sumando gente después de iniciar (unión tardía).
- **"Iniciar sesión"** → `iniciarSesion` → navega a la proyección. Deshabilitado con 0 participantes? **No:** el
  Docente puede iniciar sin nadie (no hay INV que lo impida); se advierte "Todavía no se unió nadie".
- Doble click no envía dos requests; `422 SesionYaIniciada` → navega igual a la proyección (idempotencia de cara al usuario).
- Al recargar la sala: `GET estado`; si ya está `EnCurso` redirige a la proyección, si `Finalizada` vuelve a la Comisión.
- Indicador "Reconectando…" (H8) y re-sincronización con `GET participantes` al reconectar.

---

## Especificacion del comportamiento

### Precondicion

- `US-6.3.0` (H6, H8 aprobadas), `US-6.3.1`, `US-6.3.2`, `US-6.3.4`.

### Postcondicion

- El Docente crea la sesión, ve a los participantes unirse en vivo e inicia; puede volver a una sesión activa.

---

## Criterios de aceptacion

```gherkin
Feature: Docente crea la sesión y abre la sala de espera (US-6.3.5)

  Scenario: Entrada desde el detalle de la Comisión
    Given el detalle de una Comisión del Docente
    When el Docente pulsa "+ Nueva sesión en vivo"
    Then abre el formulario con el breadcrumb de esa Comisión y sin selector de Comisión

  Scenario: Creación exitosa
    Given el formulario completo con cantidad de preguntas y tiempo límite
    When el Docente crea la sesión
    Then navega a la sala de espera con el estado EnEspera

  Scenario: Validación de cliente
    Given el formulario con tiempo límite 0
    When el Docente intenta crear
    Then ve el error y no se envía la request

  Scenario: Preguntas insuficientes
    Given un banco con menos preguntas que las pedidas
    When el Docente crea la sesión
    Then ve el mensaje del servidor y permanece en el formulario

  Scenario: Los participantes aparecen en vivo
    Given la sala de espera abierta
    When un Estudiante se une
    Then su nombre aparece como chip sin recargar

  Scenario: Iniciar la sesión
    Given la sala de espera con participantes
    When el Docente pulsa "Iniciar sesión"
    Then navega a la proyección de la primera pregunta

  Scenario: Iniciar sin participantes
    Given la sala de espera sin participantes
    When el Docente inicia
    Then ve la advertencia y la sesión se inicia igual

  Scenario: Recuperar una sesión activa
    Given una sesión EnCurso de la Comisión y el Docente que cerró la pestaña
    When abre el detalle de la Comisión
    Then ve la sesión con "Continuar" que lleva a la proyección

  Scenario: Recargar la sala con la sesión ya iniciada
    Given una sesión que ya está EnCurso
    When el Docente recarga la sala de espera
    Then es redirigido a la proyección

  Scenario: Reconexión de la sala
    Given la sala de espera y una caída del canal
    When se reconecta
    Then la lista de participantes se vuelve a cargar y desaparece el indicador
```

---

## Impacto arquitectonico

- [ ] No — pantallas sobre el cliente y el canal de `US-6.3.4`.

**Capa(s) afectadas:** [x] Frontend (sin cambios de `src/`).

**Calidad (frontend):** `oxlint`, `tsc -b`, cobertura ≥ 80%. **UAT en navegador real solo al cierre de la
iteración** (`US-6.3.10`), no por US (decisión de Víctor, Incremento 4).

---

## Fuente de verdad UX

- `docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md` §2.1 (`#doc-nueva-sesion`) y §2.2 (`#doc-sala-espera`).
- Prototipo: `docs/design/ux/prototipos/actividad-evaluativa-en-vivo.html` (`#doc-nueva-sesion`, `#doc-sala-espera`).
- **`US-6.3.0`** H6 (sesiones activas) y H8 (indicador de conexión) — **deben estar aprobados antes de codear esas partes**.
- Pantalla existente: `frontend/src/pages/actividad-evaluativa/ComisionDetalleDocente.tsx` (`docs/design/ux/wireframes-portal-entrada.md`).

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/pages/actividad-evaluativa/NuevaSesionEnVivo.tsx` (+ test) | Formulario (nuevo) |
| `frontend/src/pages/actividad-evaluativa/SalaEsperaDocente.tsx` (+ test) | Sala de espera (nueva) |
| `frontend/src/pages/actividad-evaluativa/ComisionDetalleDocente.tsx` (+ test) | Botón y bloque de sesiones activas |
| `frontend/src/router.tsx` | Reemplaza los placeholders de sala y nueva |

---

## Referencias

- Wireframes: `wireframes-actividad-evaluativa-en-vivo.md` §2.1, §2.2
- Backend: `US-6.1.2` (crear), `US-6.1.3` (unirse), `US-6.1.4` (iniciar), `US-6.3.1`, `US-6.3.2`
- Depende de: `US-6.3.0`, `US-6.3.1`, `US-6.3.2`, `US-6.3.4`
- Consumida por: `US-6.3.6`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
