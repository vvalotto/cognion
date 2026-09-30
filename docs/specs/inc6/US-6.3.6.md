# US-6.3.6: Docente proyecta la pregunta, muestra las opciones y la cierra

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-6.3`
**Tipo**: `feat frontend`
**Agregado principal afectado**: — (consume `MostrarOpcionesDeLaPregunta` y `CerrarPreguntaActual`)
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **proyectar la pregunta al aula, mostrar las opciones cuando yo decida y cerrarla cuando terminó el tiempo**,
para **conducir el ritmo de la clase desde una sola pantalla**.

---

## Contexto del dominio

### Problema

Es la primera mitad de la **pantalla de proyección** (`StageLayout`, `US-6.3.4`): la que ve toda el aula. Esta US
crea el **contenedor** `ProyeccionSesionEnVivo` con su máquina de etapas y las dos primeras etapas; `US-6.3.7`
agrega las restantes (histograma, ranking, final) **sobre el mismo contenedor**.

### Etapa del contenedor (se decide al cargar y en cada mensaje)

Al montar y en cada `onReconectado` el contenedor pide `GET estado` (`US-6.3.3`) y calcula la etapa; luego la
mantiene con los mensajes del canal:

| Estado del servidor | Etapa |
|---|---|
| `EnCurso`, con pregunta, `opciones_mostradas = false` | `#stage-pregunta-sola` |
| `EnCurso`, `opciones_mostradas = true`, `pregunta_actual_cerrada = false` | `#stage-pregunta-opciones` |
| `EnCurso`, `pregunta_actual_cerrada = true` | histograma/ranking (**`US-6.3.7`**) |
| `Finalizada` | resultado final (**`US-6.3.7`**) |
| `EnEspera` | redirige a la sala |

### `#stage-pregunta-sola` (§2.3)

- Enunciado en tipografía de proyección (**≥ 40 px**, §1.1), eyebrow "Pregunta N de total" (≥ 18-20 px, mayúsculas).
  **Sin opciones todavía.**
- Botón **"Mostrar opciones"** → `mostrarOpciones` → etapa siguiente. El temporizador arranca **recién ahí** (INV-AEV-08).
- Doble click no envía dos requests; `422 OpcionesYaMostradas` → pasa igual a la etapa siguiente.

### `#stage-pregunta-opciones` (§2.4, con H1 y H2 de `US-6.3.0`)

- Enunciado más chico + **opciones como cajas de color sólido** (`a` rojo, `b` azul, `c` amarillo, `d` verde), texto
  completo dentro, **sin ícono de forma, sin indicar la correcta**. **Verdadero/Falso:** dos cajas ("Verdadero" `b`,
  "Falso" `c`). **3 opciones:** colores `a`,`b`,`c` (según lo que apruebe `US-6.3.0`).
- **Temporizador** (≥ 26 px) con cuenta regresiva y **barra de progreso**. Tiempo restante:
  - **en vivo:** arranca al recibir `opciones_mostradas` con `tiempoLimitePorPreguntaSegundos`;
  - **tras recargar:** `tiempoLimite − (ahora − opcionesMostradasEn)` con el `GET estado`, acotado a ≥ 0.
  Es **informativo para el aula**: el corte real es del servidor (INV-AEV-08); un reloj de cliente desfasado no cambia
  qué respuestas se aceptan. Al llegar a 0 **no cierra solo** — el Docente decide.
- **Conteo** "`N` / `total` ya respondieron": `N` de `cantidadRespuestas` (estado inicial y `conteo_respuestas_actualizado`),
  `total` de `totalParticipantes` (estado inicial y `participantes_actualizados`). **Solo el total**, sin desglose por opción.
- Botón **"Cerrar pregunta"** (estilo destructivo, deliberado) → `cerrarPregunta`. La respuesta HTTP no trae el resultado:
  la etapa siguiente se dispara con el mensaje `pregunta_cerrada` del canal, y si no llega en 2 s se recalcula con `GET estado`.
  `422 PreguntaYaCerrada` → recalcula con `GET estado`.

### Legibilidad (§1.1)

Tokens `--stage-*`; contraste ≥ 7:1 (AAA); una sola columna centrada, **sin scroll**, máximo 3-4 elementos por pantalla.
Los tamaños mínimos se aplican con clases/tokens y se **verifican en navegador real** (`US-6.3.10`); jsdom no calcula estilos.

---

## Especificacion del comportamiento

### Precondicion

- `US-6.3.0` (H1, H2, H8), `US-6.3.3`, `US-6.3.4`, `US-6.3.5` cerradas.

### Postcondicion

- El Docente proyecta la pregunta, muestra las opciones con temporizador y conteo en vivo y la cierra.

---

## Criterios de aceptacion

```gherkin
Feature: Docente proyecta la pregunta y controla las opciones (US-6.3.6)

  Scenario: Pregunta sola
    Given una sesión recién iniciada
    When el Docente abre la proyección
    Then ve el enunciado grande, "Pregunta 1 de N" y el botón "Mostrar opciones", sin opciones

  Scenario: Mostrar las opciones arranca el temporizador
    Given la pregunta sola en pantalla
    When el Docente pulsa "Mostrar opciones"
    Then aparecen las opciones como cajas de color y el temporizador cuenta desde el tiempo límite

  Scenario: Las opciones no revelan la correcta
    Given la pregunta con opciones
    When se observa la pantalla
    Then ninguna opción está marcada como correcta

  Scenario: Verdadero/Falso
    Given una pregunta de Verdadero/Falso con las opciones mostradas
    When se observa la pantalla
    Then hay dos cajas, "Verdadero" y "Falso"

  Scenario: El conteo se actualiza en vivo
    Given la pregunta con opciones y 5 participantes
    When llegan 3 respuestas
    Then el conteo muestra "3 / 5 ya respondieron"

  Scenario: El temporizador en 0 no cierra la pregunta
    Given la pregunta con el temporizador en cero
    When pasan segundos más
    Then la pregunta sigue abierta hasta que el Docente pulsa "Cerrar pregunta"

  Scenario: Cerrar la pregunta
    Given la pregunta con opciones
    When el Docente pulsa "Cerrar pregunta"
    Then se envía el comando y la pantalla pasa a la etapa de resultado

  Scenario: Recargar en medio de la pregunta
    Given la pregunta con opciones abierta hace 10 segundos
    When el Docente recarga la proyección
    Then vuelve a la misma etapa con el temporizador descontando esos 10 segundos y el conteo actual

  Scenario: Doble click en "Mostrar opciones"
    Given la pregunta sola
    When el Docente hace doble click
    Then se envía una sola request

  Scenario: Reconexión
    Given la proyección con el canal caído
    When se reconecta
    Then la etapa y el conteo se recalculan desde el estado del servidor
```

---

## Impacto arquitectonico

- [ ] No.

**Capa(s) afectadas:** [x] Frontend (sin cambios de `src/`).

**Calidad (frontend):** `oxlint`, `tsc -b`, cobertura ≥ 80%; tests con `vi.useFakeTimers()` para el temporizador; canal falso.

---

## Fuente de verdad UX

- `docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md` §1 (identidad), §1.1 (legibilidad en proyección), §2.3 (`#stage-pregunta-sola`), §2.4 (`#stage-pregunta-opciones`).
- Prototipo: `#stage-pregunta-sola`, `#stage-pregunta-opciones`.
- **`US-6.3.0`** H1 (V/F), H2 (3 opciones), H8 (conexión) — aprobados antes de codear esas variantes.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/pages/actividad-evaluativa/ProyeccionSesionEnVivo.tsx` (+ test) | Contenedor y máquina de etapas (nuevo) |
| `frontend/src/pages/actividad-evaluativa/proyeccion/StagePreguntaSola.tsx`, `StagePreguntaOpciones.tsx` (+ tests) | Etapas (nuevas) |
| `frontend/src/lib/temporizador-pregunta.ts` (+ test) | Cálculo del tiempo restante (compartido con `US-6.3.9`) |
| `frontend/src/lib/opciones-en-vivo.ts` (+ test) | Mapa opción → color, V/F y N opciones (compartido con `US-6.3.9`) |
| `frontend/src/router.tsx` | Reemplaza el placeholder de proyección |

---

## Referencias

- Wireframes: `wireframes-actividad-evaluativa-en-vivo.md` §1.1, §2.3, §2.4
- Backend: `US-6.2.2` (mostrar opciones), `US-6.2.5` (cerrar), `US-6.3.3` (estado completo)
- Depende de: `US-6.3.0`, `US-6.3.3`, `US-6.3.4`, `US-6.3.5`
- Consumida por: `US-6.3.7`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
