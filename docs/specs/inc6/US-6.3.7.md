# US-6.3.7: Docente proyecta histograma, ranking y resultado final; avanza o finaliza

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-6.3`
**Tipo**: `feat frontend`
**Agregado principal afectado**: — (consume `AvanzarSiguientePregunta` y `FinalizarSesionEnVivo`)
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **mostrarle al aula cómo respondió la clase, quién va ganando y el resultado final**,
para **cerrar cada pregunta con un momento de discusión y terminar la dinámica con el podio**.

---

## Contexto del dominio

### Problema

Segunda mitad de la proyección: completa la máquina de etapas del contenedor `ProyeccionSesionEnVivo`
(`US-6.3.6`) con el resultado tras cerrar la pregunta y el final de la sesión.

### `#stage-histograma` (§2.5)

- Una **barra por opción** con la cantidad de Estudiantes que la eligieron, del **mismo color sólido** que su caja en
  `#stage-pregunta-opciones`; la **correcta remarcada** con borde blanco y `✓`.
- Datos: `distribucion` y `respuestaCorrecta` del mensaje `pregunta_cerrada`; tras recargar, `resultado_pregunta` del
  `GET estado` (`US-6.3.3`).
- `distribucion.opcion` es el índice como texto o `"verdadero"`/`"falso"`; las opciones **sin respuestas** se
  muestran igual, con barra de 0 (el servidor solo manda las que tienen cantidad ≥ 1: el cliente completa el resto
  con las opciones de `respuestaCorrecta.opciones`).
- **Transición automática al ranking a los pocos segundos** (confirmado con Víctor): es presentación pura, no un
  comando — un temporizador local de **6 s** (constante `SEGUNDOS_HISTOGRAMA`). Botón **"Ver ranking ahora"** la adelanta.

### `#stage-ranking` (§2.6) — **Top 3** (decidido con Víctor, 2026-09-21)

- Ranking con **nombre y puntaje acumulado**, orden descendente, **tantos puestos como participantes haya** hasta 3
  (`US-6.3.0` H9); con 0 participantes: "Nadie participó".
- Botón **"Siguiente pregunta"** si quedan preguntas (`preguntaActualIndice + 1 < cantidadPreguntas`) →
  `avanzarPregunta` → vuelve a `#stage-pregunta-sola` con la pregunta siguiente. `422 NoQuedanPreguntas` → recalcula
  con `GET estado`.
- Botón **"Finalizar sesión"** **siempre visible** (se puede terminar antes de agotar el set, decidido 2026-09-21) →
  `finalizarSesion` → etapa final. Estilo deliberado y separado de "Siguiente pregunta".

### `#stage-final` (§2.7)

- **Podio Top 3** con el formato clásico (1°/2°/3°, alturas distintas) y **"¡Gracias por participar!"**; datos del
  mensaje `sesion_finalizada` o, tras recargar, de `GET .../ranking`.
- Pantalla terminal para el aula. Enlace discreto **"Volver a la Comisión"** fuera del foco (H7 de `US-6.3.0`).
- Sin exportar ni comparar históricos (fuera de alcance: eso es Analytics).

### Resolución de la etapa tras cerrar (mismo criterio que `US-6.3.6`)

El paso a histograma se dispara con `pregunta_cerrada`; si no llega en 2 s, se recalcula con `GET estado`. Recargar en
cualquier etapa posterior al cierre reconstruye **histograma** (si el Docente todavía no pasó al ranking, se vuelve a
mostrar el histograma con su temporizador) o **ranking**, según lo que devuelva `resultado_pregunta`; el cliente no
recuerda a cuál de las dos había llegado (es presentación, no estado de dominio).

---

## Especificacion del comportamiento

### Precondicion

- `US-6.3.6` cerrada (el contenedor); `US-6.3.1` y `US-6.3.3` (nombres y `resultado_pregunta`).

### Postcondicion

- El Docente conduce toda la sesión hasta el podio final desde la proyección.

---

## Criterios de aceptacion

```gherkin
Feature: Docente proyecta histograma, ranking y resultado final (US-6.3.7)

  Scenario: El histograma muestra la distribución y marca la correcta
    Given una pregunta cerrada con respuestas repartidas
    When se muestra el resultado
    Then hay una barra por opción con su cantidad y la correcta lleva borde blanco y ✓

  Scenario: Opciones sin respuestas se muestran en cero
    Given una opción que nadie eligió
    When se muestra el histograma
    Then aparece con barra de 0

  Scenario: Paso automático al ranking
    Given el histograma en pantalla
    When pasan 6 segundos
    Then la pantalla pasa al ranking

  Scenario: Adelantar el ranking
    Given el histograma en pantalla
    When el Docente pulsa "Ver ranking ahora"
    Then pasa al ranking de inmediato

  Scenario: Ranking Top 3 con nombres
    Given 6 participantes con puntajes distintos
    When se muestra el ranking
    Then aparecen solo los 3 primeros, con nombre y puntaje, en orden descendente

  Scenario: Menos de 3 participantes
    Given 2 participantes
    When se muestra el ranking
    Then aparecen esos 2

  Scenario: Nadie participó
    Given una pregunta que nadie respondió y sin participantes
    When se muestra el ranking
    Then dice "Nadie participó"

  Scenario: Siguiente pregunta
    Given el ranking con preguntas restantes
    When el Docente pulsa "Siguiente pregunta"
    Then vuelve a la pregunta sola con la siguiente pregunta

  Scenario: En la última pregunta no hay "Siguiente"
    Given el ranking de la última pregunta
    When se observa la pantalla
    Then solo está "Finalizar sesión"

  Scenario: Finalizar antes de tiempo
    Given el ranking en la pregunta 2 de 5
    When el Docente pulsa "Finalizar sesión"
    Then se muestra el podio final

  Scenario: Podio final
    Given la sesión finalizada
    When se muestra el resultado final
    Then se ve el podio Top 3 con nombres y "¡Gracias por participar!"

  Scenario: Recargar tras el cierre
    Given una pregunta cerrada y el Docente que recarga la proyección
    When vuelve a cargar
    Then recupera el histograma o el ranking sin perder los datos

  Scenario: Recargar con la sesión finalizada
    Given una sesión finalizada
    When el Docente abre la proyección
    Then ve el podio final
```

---

## Impacto arquitectonico

- [ ] No.

**Capa(s) afectadas:** [x] Frontend (sin cambios de `src/`).

**Calidad (frontend):** `oxlint`, `tsc -b`, cobertura ≥ 80%; `vi.useFakeTimers()` para los 6 s del histograma.

---

## Fuente de verdad UX

- `docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md` §1.1, §2.5 (`#stage-histograma`), §2.6 (`#stage-ranking`), §2.7 (`#stage-final`).
- Prototipo: `#stage-histograma`, `#stage-ranking`, `#stage-final`.
- **`US-6.3.0`** H7 (salida) y H9 (menos de 3 participantes). Top 3 en toda pantalla: decisión de Víctor (2026-09-21) que resuelve el "a definir en la spec" de §2.6.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/pages/actividad-evaluativa/proyeccion/StageHistograma.tsx`, `StageRanking.tsx`, `StageFinal.tsx` (+ tests) | Etapas (nuevas) |
| `frontend/src/pages/actividad-evaluativa/ProyeccionSesionEnVivo.tsx` (+ test) | Etapas nuevas en la máquina |
| `frontend/src/lib/opciones-en-vivo.ts` | Completar distribución con opciones sin respuestas |

---

## Referencias

- Wireframes: `wireframes-actividad-evaluativa-en-vivo.md` §2.5, §2.6, §2.7
- Backend: `US-6.2.5`, `US-6.2.6`, `US-6.2.7`, `US-6.3.1`, `US-6.3.3`
- Depende de: `US-6.3.6`, `US-6.3.0`
- Consumida por: `US-6.3.10`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
