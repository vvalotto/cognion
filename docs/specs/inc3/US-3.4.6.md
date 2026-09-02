# US-3.4.6: Estudiante rinde su evaluación — responde, pausa y reanuda

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-3.4`
**Tipo**: `feat backend + frontend`
**Agregado principal afectado**: `Evaluacion` (respuesta de lectura ampliada, sin cambios de invariantes)
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Estudiante**,
quiero **responder mis preguntas una a una, con la certeza de que cada respuesta confirmada
queda guardada, y poder pausar y retomar sin perder nada**
para **rendir la evaluación de forma confiable aunque se corte la conexión (RNF Confiabilidad,
RF-12)**.

---

## Contexto del dominio

### Problema

`POST /evaluaciones` (iniciar/retomar, `US-3.1.3`), `POST /evaluaciones/{id}/respuestas`
(`US-3.2.1`) y `POST /evaluaciones/{id}/suspender`+`/reanudar` (`US-3.2.2`) ya existen y no
cambian de comportamiento — pero sus *respuestas* no traen lo que esta pantalla necesita
mostrar:

- `PreguntaAsignadaResponse` (dentro de `EvaluacionResponse`) solo trae `pregunta_id` + `orden`
  — sin el enunciado ni las opciones, el frontend no tiene qué renderizar en la `Card` de
  pregunta (wireframe §3.3).
- `EvaluacionResponse` no expone qué preguntas ya tienen `Respuesta` confirmada — sin eso no se
  puede pintar el indicador de puntos (`.dot`, verde/azul/gris) del wireframe.

Ninguno de los dos gaps requiere un endpoint nuevo — son campos que faltan en los `response`
existentes.

**Contenido de la pregunta:** `PreguntaConsultaPort` ya tiene `obtener_detalle_correccion()`
(`US-3.2.3`), pero ese método devuelve `contenido_correcto` — filtrarlo para ocultar la
respuesta correcta antes de finalizar sería frágil (un cambio ahí podría filtrar la respuesta
por error). Se agrega un método nuevo, explícitamente sin la respuesta correcta:

| Puerto | Método nuevo | Motivo |
|---|---|---|
| `PreguntaConsultaPort` | `obtener_contenido(pregunta_id) -> ContenidoPregunta` (`texto`, `opciones` — sin respuesta correcta) | `obtener_detalle_correccion()` expone la respuesta correcta; no debe reusarse antes de finalizar (hot spot del modelo, §5 — "sin feedback de corrección") |

**Respuestas ya dadas:** el aggregate `Evaluacion` ya trackea `respuestas: list[Respuesta]`
desde `US-3.2.1` (persistencia atómica, respuesta a respuesta) — no hace falta un puerto nuevo,
solo exponer `pregunta_id`s ya respondidas en `EvaluacionResponse`.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Endpoints reutilizados | `POST /evaluaciones`, `POST /evaluaciones/{id}/respuestas`, `.../suspender`, `.../reanudar` | Ya existen, sin cambios de comportamiento |
| Response ampliado | `PreguntaAsignadaResponse` | Agrega `enunciado`, `opciones` (poblado vía `PreguntaConsultaPort.obtener_contenido()`) |
| Response ampliado | `EvaluacionResponse` | Agrega `preguntas_respondidas: list[UUID]` (de `Evaluacion.respuestas`) |

---

## Especificacion del comportamiento

### Precondicion

- `US-3.4.5` implementada (se entra desde el listado de actividades del Estudiante).
- `Evaluacion` iniciada (o retomada) para la actividad elegida.

### Postcondicion

- `#est-rendir`: barra de progreso + card de la pregunta actual + navegación por puntos
  (verde=respondida, azul=actual, gris=pendiente) + "Anterior"/"Confirmar y siguiente".
- Confirmar una respuesta → `POST /evaluaciones/{id}/respuestas`, avanza a la siguiente
  pregunta sin perder las anteriores ante un refresh (`IniciarEvaluacion` es idempotente,
  `US-3.1.3`).
- "Pausar y salir" → `POST .../suspender`, navega a `#est-suspendida` (`US-3.2.2`).
- Reconexión (recarga de página o vuelta después de un corte) → llama `POST /evaluaciones` de
  nuevo, retoma en el mismo punto sin regenerar el set (INV-AE-05/06).

### Invariantes

| ID | Invariante |
|----|------------|
| — | Ninguna opción muestra si es correcta al responder — el `Badge` de corrección solo aparece en la revisión (`US-3.4.7`, RF-13). |
| — | Una pregunta con `cantidad_intentos_permitidos` agotados se muestra sin opción de reenviar (detalle de estado, wireframe §3.3, no bloqueante para esta spec). |

---

## Criterios de aceptacion

```gherkin
Feature: Rendir evaluación (US-3.4.6)

  Scenario: Confirmar una respuesta
    Given un Estudiante en #est-rendir, en la pregunta actual
    When elige una opción y confirma
    Then el sistema persiste la Respuesta de inmediato
    And avanza a la siguiente pregunta

  Scenario: Reconexión sin pérdida
    Given un Estudiante que ya confirmó 3 de 10 respuestas
    When recarga la página o vuelve a entrar más tarde
    Then retoma en la misma Evaluacion, con las 3 respuestas ya marcadas como respondidas
    And sin que se genere un nuevo set de preguntas

  Scenario: Pausar y salir
    Given un Estudiante en #est-rendir
    When toca "Pausar y salir"
    Then el sistema suspende la Evaluacion
    And navega a #est-suspendida

  Scenario: Reanudar desde suspendida
    Given un Estudiante con una Evaluacion Suspendida
    When toca "Continuar" en #est-suspendida
    Then vuelve a #est-rendir en el mismo punto donde quedó
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — extiende dos `response` existentes y agrega un método de solo lectura a un puerto ya
  existente, sin tocar invariantes de dominio ni comandos.

**Capa(s) afectadas:**
- [x] Backend — `entities/ports/pregunta_consulta_port.py` (método nuevo),
  `frameworks/api/schemas.py` (campos nuevos en dos `response`),
  `use_cases/iniciar_evaluacion.py` (puebla el contenido al construir el `response`)
- [x] Frontend — `frontend/src/pages/RendirEvaluacion.tsx`, `EvaluacionSuspendida.tsx`

---

## Fuente de verdad UX

`docs/design/ux/wireframes-actividad-evaluativa.md` §3.3 (`#est-rendir`), §3.4
(`#est-suspendida`). Prototipo:
`docs/design/ux/prototipos/actividad-evaluativa-periodo-abierto.html`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/actividad_evaluativa/entities/ports/pregunta_consulta_port.py` | Agrega `obtener_contenido(pregunta_id)`, `ContenidoPregunta` |
| `src/actividad_evaluativa/frameworks/api/schemas.py` | `PreguntaAsignadaResponse` +`enunciado`/`opciones`; `EvaluacionResponse` +`preguntas_respondidas` |
| `src/actividad_evaluativa/use_cases/iniciar_evaluacion.py` | Puebla los campos nuevos del response |
| `frontend/src/pages/RendirEvaluacion.tsx` | Nueva — card de pregunta, navegación por puntos, progreso |
| `frontend/src/pages/EvaluacionSuspendida.tsx` | Nueva — mensaje + "Continuar" |
| `frontend/src/router.tsx` | Rutas `/mis-actividades/:actividadId/rendir`, `/mis-actividades/:actividadId/suspendida` |

---

## Referencias

- Relacionada con: `US-3.1.3`, `US-3.2.1`, `US-3.2.2` (backend reutilizado y extendido), `US-3.4.5` (navegación de entrada)
- Candidatas: `docs/plans/inc3/inc3-candidatas.md` §Iteración 4

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
