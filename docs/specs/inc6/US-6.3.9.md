# US-6.3.9: Estudiante responde desde el celular y ve su resultado y el final

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-6.3`
**Tipo**: `feat frontend`
**Agregado principal afectado**: — (consume `ResponderPreguntaEnVivo`)
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Estudiante**,
quiero **responder tocando una tarjeta de color, ver enseguida si acerté y cuántos puntos gané, y al final ver mi posición**,
para **participar de la dinámica desde mi celular sin perder el ritmo de la clase**.

---

## Contexto del dominio

### Problema

Cubre `§3.3 #est-pregunta`, `§3.4 #est-resultado-pregunta` y `§3.5 #est-resultado-final`, más las etapas que
`US-6.3.0` agrega (H3, H4, H5). Completa la máquina de etapas del contenedor `SesionEnVivoEstudiante` (`US-6.3.8`).
Es la **US frontend más grande de la iteración**; si en la Fase 2 el plan supera el alcance razonable, se divide en
"responder + resultado de la pregunta" y "resultado final + reconexión" sin cambiar el contrato.

### Etapas (se recalculan con `GET estado` al montar y en cada `onReconectado`, y siguen los mensajes del canal)

| Estado / mensaje | Etapa |
|---|---|
| `pregunta_presentada` (opciones ocultas) | **`#est-espera-opciones`** (H3): "Pregunta N de total" + enunciado + "Esperá a que el Docente muestre las opciones" |
| `opciones_mostradas` y **no** respondió | **`#est-pregunta`** |
| respondió (`ya_respondio`) | **`#est-resultado-pregunta`** |
| `pregunta_cerrada` y **no** respondió, o `TiempoAgotado` | **`#est-sin-respuesta`** (H4, H5) |
| `sesion_finalizada` / `Finalizada` | **`#est-resultado-final`** |
| `pregunta_presentada` siguiente | vuelve a `#est-espera-opciones` |

### `#est-pregunta` (§3.3, con H1 y H2)

- Barra de progreso + "Pregunta N de total"; **temporizador personal** (mismo cálculo que la proyección,
  `lib/temporizador-pregunta.ts`, `US-6.3.6`), **informativo** — el corte es del servidor (INV-AEV-08).
- **Tarjetas táctiles** (`.tap-card`), grilla **2×2**, del **mismo color sólido que ve la proyección** (`a` rojo,
  `b` azul, `c` amarillo, `d` verde) con el texto completo de la opción. **Verdadero/Falso:** 2 tarjetas; **3 opciones:**
  la tercera ocupa el ancho completo (`lib/opciones-en-vivo.ts`).
- **Tocar responde al instante**, sin botón "Confirmar" (tercera ronda de `US-6.0.2`): dispara `responderPregunta` con
  `{opcion_indice}` o `{valor}` y pasa al resultado. **Un solo intento** (INV-AEV-07): tras el primer toque se deshabilitan
  todas las tarjetas (no hay doble envío).
- Hint: "Tocá una tarjeta para responder — un solo intento, no se puede cambiar después".

### `#est-resultado-pregunta` (§3.4) — inmediato y **sin ranking** (cuarta ronda)

- Con la respuesta del `POST`: ícono + **"¡Correcto!" / "Incorrecto"**, **"+N puntos en esta pregunta"** y **"Llevás
  acumulados: X pts"**. **No** se muestra la posición ni el top: el ranking queda reservado al resultado final.
- Se mantiene hasta `pregunta_presentada` (siguiente) o `sesion_finalizada`. **No** revela la respuesta correcta.
- Errores del `POST`:
  - `422 TiempoAgotado` → **`#est-sin-respuesta`** con "Se acabó el tiempo antes de tu respuesta" (H5);
  - `422 RespuestaYaRegistrada` / `PreguntaYaCerrada` → recalcula con `GET estado` (`ya_respondio`, `puntaje_acumulado`); si no
    conoce el puntaje de esa pregunta muestra solo el acumulado;
  - `404 ParticipacionNoExiste` → vuelve a llamar a `unirseASesion` y reintenta la etapa.

### `#est-sin-respuesta` (H4, H5)

- "Se cerró la pregunta — no respondiste (+0)" (o el mensaje de tiempo agotado) y el **acumulado propio**; espera la
  siguiente pregunta o el final. Sin ranking.

### `#est-resultado-final` (§3.5) — **Top 3** (decidido con Víctor, 2026-09-21)

- **"Quedaste N° con X puntos"**, destacado: la posición sale del `ranking` completo (`sesion_finalizada` o `GET .../ranking`,
  que el Estudiante puede consultar solo con la sesión `Finalizada`).
- **Top 3** con nombres, **con la fila propia resaltada**; si el Estudiante quedó fuera del Top 3, su fila se agrega
  debajo con su posición. Sin revisión pregunta por pregunta (fuera de alcance de RF-08/09/10).

### Reconexión del celular

El celular pierde señal seguido. Al reconectar se pide `GET estado` y se **recalcula la etapa**: recupera la pregunta actual, el
tiempo restante (`opcionesMostradasEn` + límite), su avance (`ya_respondio`, `puntaje_acumulado`) y **no pierde su participación**.
Indicador "Reconectando…" discreto (H8).

---

## Especificacion del comportamiento

### Precondicion

- `US-6.3.0` (H1 a H5, H8), `US-6.3.1`, `US-6.3.6` (`temporizador-pregunta`, `opciones-en-vivo`), `US-6.3.8` cerradas.

### Postcondicion

- El Estudiante responde una vez por pregunta, ve su resultado al instante y su posición al final.

---

## Criterios de aceptacion

```gherkin
Feature: Estudiante responde y ve su resultado (US-6.3.9)

  Scenario: Espera de opciones
    Given una pregunta presentada sin opciones
    When el Estudiante la mira
    Then ve "Pregunta N de total", el enunciado y el mensaje de espera

  Scenario: Aparecen las tarjetas
    Given la espera de opciones
    When llega opciones_mostradas
    Then aparecen las tarjetas de color y arranca el temporizador

  Scenario: Responder con un toque
    Given las tarjetas visibles
    When el Estudiante toca una
    Then se envía la respuesta sin pedir confirmación y ve su resultado

  Scenario: Un solo intento
    Given una respuesta enviada
    When el Estudiante intenta tocar otra tarjeta
    Then las tarjetas están deshabilitadas y no se envía nada

  Scenario: Verdadero/Falso
    Given una pregunta de Verdadero/Falso
    When se muestran las opciones
    Then hay dos tarjetas y responde con el valor booleano

  Scenario: Tres opciones
    Given una pregunta de 3 opciones
    When se muestran las opciones
    Then hay tres tarjetas y la tercera ocupa el ancho completo

  Scenario: Resultado correcto sin ranking
    Given una respuesta correcta
    When se muestra el resultado
    Then ve "¡Correcto!", los puntos de la pregunta y su acumulado, sin ranking ni posición

  Scenario: Resultado incorrecto
    Given una respuesta incorrecta
    When se muestra el resultado
    Then ve "Incorrecto" y +0 puntos

  Scenario: Tiempo agotado al tocar
    Given un toque fuera del tiempo límite
    When el servidor responde TiempoAgotado
    Then ve "Se acabó el tiempo" con su acumulado

  Scenario: No respondió y se cerró la pregunta
    Given una pregunta abierta que el Estudiante dejó pasar
    When llega pregunta_cerrada
    Then ve "no respondiste (+0)" con su acumulado

  Scenario: Pasa a la siguiente pregunta solo
    Given el resultado de una pregunta
    When llega pregunta_presentada
    Then vuelve a la espera de opciones de la nueva pregunta

  Scenario: Resultado final con posición
    Given la sesión finalizada
    When el Estudiante ve el resultado final
    Then ve "Quedaste N° con X puntos", el Top 3 con nombres y su fila resaltada

  Scenario: Fuera del Top 3
    Given un Estudiante que quedó 5°
    When ve el resultado final
    Then ve el Top 3 y su propia fila con su posición debajo

  Scenario: Reconexión con la pregunta abierta
    Given un Estudiante que pierde la conexión con la pregunta abierta
    When se reconecta
    Then recupera la pregunta, el tiempo restante y su avance sin perder su participación

  Scenario: Recarga después de responder
    Given un Estudiante que ya respondió
    When recarga la pantalla
    Then ve su resultado y no puede volver a responder
```

---

## Impacto arquitectonico

- [ ] No.

**Capa(s) afectadas:** [x] Frontend (sin cambios de `src/`).

**Calidad (frontend):** `oxlint`, `tsc -b`, cobertura ≥ 80%. Diseñada **para pulgar**: objetivos táctiles ≥ 44 px,
verificados en un **celular real** en `US-6.3.10`.

---

## Fuente de verdad UX

- `docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md` §3.3 (`#est-pregunta`), §3.4 (`#est-resultado-pregunta`), §3.5 (`#est-resultado-final`).
- Prototipo: `#est-pregunta`, `#est-resultado-pregunta`, `#est-resultado-final` (`.tap-card.color-a/b/c/d`).
- **`US-6.3.0`** H1, H2 (V/F y 3 opciones), H3 (`#est-espera-opciones`), H4/H5 (`#est-sin-respuesta`), H8 (conexión), H9.
- Top 3 en el resultado final: decisión de Víctor (2026-09-21).

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/pages/actividad-evaluativa/estudiante/EsperaOpciones.tsx`, `PreguntaActiva.tsx`, `ResultadoPregunta.tsx`, `SinRespuesta.tsx`, `ResultadoFinal.tsx` (+ tests) | Etapas (nuevas) |
| `frontend/src/pages/actividad-evaluativa/SesionEnVivoEstudiante.tsx` (+ test) | Etapas nuevas en la máquina |
| `frontend/src/lib/temporizador-pregunta.ts`, `opciones-en-vivo.ts` | Reutilizados de `US-6.3.6` |

---

## Referencias

- Wireframes: `wireframes-actividad-evaluativa-en-vivo.md` §3.3, §3.4, §3.5
- Backend: `US-6.2.4` (responder), `US-6.2.8` (estado, ranking), `US-6.3.1` (nombres)
- Depende de: `US-6.3.8`, `US-6.3.6`, `US-6.3.0`, `US-6.3.1`
- Consumida por: `US-6.3.10`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
