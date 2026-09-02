# US-ADJ-12: Fix — RendirEvaluacion no muestra la respuesta previa ni avanza al revisitar una pregunta ya respondida

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-3.4` (ajuste inmediato, detectado en la propia revisión manual de
Víctor sobre la Iteración 4 — mismo criterio que `US-ADJ-09`/`10`/`11`, no forma parte de un
`SP-ADJ` diferido)
**Tipo**: `fix full-stack` (backend interface_adapters/frameworks + frontend)
**Agregado principal afectado**: ninguno — sin cambios de dominio ni de invariantes. Reutiliza
`Evaluacion.respuesta_vigente_de` (`US-3.2.3`), ya existente.
**Bounded Context**: Actividad Evaluativa
**Origen**: revisión manual de Víctor sobre el checklist
`quality/reports/uat/inc3/guion-manual-iteracion4.md`, 2026-09-02. Issue
[#199](https://github.com/vvalotto/cognion/issues/199).

---

## Descripcion (lenguaje de negocio)

Como **Estudiante**,
quiero **que al volver a una pregunta que ya respondí vea mi respuesta y pueda seguir
navegando**
para **no quedar bloqueado en medio de la evaluación solo por haber usado el botón
"Anterior" para revisar lo que ya contesté**.

---

## Contexto del dominio

### Problema (dos síntomas del mismo bug de UI)

`RendirEvaluacion.tsx` (`US-3.4.6`) guarda la selección del Estudiante en una única variable de
estado local (`seleccion`), sin memoria por pregunta. Escenario reproducido:

1. Responde la pregunta 1 y confirma (`registrarRespuesta`) → avanza a la 2.
2. Selecciona una opción en la pregunta 2, **sin confirmar**.
3. Toca "Anterior" → vuelve a la pregunta 1.

**Síntoma 1 — no muestra la respuesta previa:** al volver, `seleccion` está en `null` (se limpia
en `irA`) — la pantalla no refleja lo que ya había confirmado. Esto no es solo un olvido de
frontend: **el backend tampoco expone esa información**. `EvaluacionResponse` solo trae
`preguntas_respondidas: list[UUID]` (ids, sin contenido) — no hay de dónde reconstruir la
selección aunque el frontend quisiera guardarla localmente antes de navegar.

**Síntoma 2 — no puede avanzar:** al reintentar confirmar la pregunta 1 (ya respondida,
`cantidad_intentos_permitidos = 1` en toda actividad creada hasta hoy), el backend rechaza
correctamente con `422 IntentosAgotados` (INV-AE-07/08, comportamiento de dominio correcto y
sin cambios). Pero `confirmarYSiguiente` corta en el `catch` sin avanzar `indiceActual` — el
único camino de la UI para progresar pasa por ese botón, así que el Estudiante queda
efectivamente trabado.

### Alcance del fix

**Backend** (`src/actividad_evaluativa/frameworks/api/`, capas `interface_adapters`/
`frameworks` — sin tocar `entities`/`use_cases`): agregar a `EvaluacionResponse` el contenido de
la respuesta vigente por pregunta, reutilizando `Evaluacion.respuesta_vigente_de(pregunta_id)`
(ya usado por la revisión, `US-3.2.3`) desde el adaptador `_a_response` que ya arman los 4
endpoints de `evaluaciones_router.py`. No expone `es_correcta` — mismo criterio de "sin
feedback inmediato" que `RespuestaResponse` (`BC-actividad-evaluativa-modelo.md` §5): el
Estudiante ve su **propia** elección, nunca si acertó.

**Frontend** (`RendirEvaluacion.tsx`): al entrar o navegar (`irA`) a una pregunta que ya está en
`preguntasRespondidas`, prellenar `seleccion` desde el contenido confirmado que ahora trae la
API, deshabilitar los inputs (modo solo lectura — no tiene sentido reofrecer una elección que no
se puede volver a confirmar) y hacer que el botón navegue (a la siguiente pregunta, o finalice
si es la última) **sin** volver a llamar `registrarRespuesta`.

**Fuera de alcance:** soporte de múltiples intentos por pregunta en la UI (cambiar de opinión y
volver a confirmar). Ninguna actividad creada hasta hoy usa
`cantidad_intentos_permitidos > 1` — si eso cambia en el futuro, es una US aparte.

---

## Especificacion del comportamiento

### Precondicion

- Una `Evaluacion` `EnCurso` con al menos una `Respuesta` confirmada para alguna
  `PreguntaAsignada`.

### Postcondicion

- `EvaluacionResponse` (los 4 endpoints que lo devuelven: iniciar, suspender, reanudar,
  finalizar) incluye el contenido de la respuesta vigente de cada pregunta ya respondida.
- En el frontend, revisitar una pregunta ya respondida muestra la opción/valor que el
  Estudiante había confirmado, con los inputs deshabilitados.
- El botón, sobre una pregunta ya respondida, navega a la siguiente (o finaliza si es la
  última) sin llamar a `POST /evaluaciones/{id}/respuestas`.
- Sobre una pregunta **no** respondida el comportamiento no cambia: inputs habilitados, el
  botón sigue llamando a `registrarRespuesta` antes de avanzar.

### Invariantes

Ninguna nueva — no hay cambio de dominio. La invariante que ya rige (INV-AE-07/08,
`IntentosAgotados`) deja de dispararse en este flujo simplemente porque el frontend deja de
reintentar una confirmación redundante, no porque el backend cambie su validación.

---

## Criterios de aceptacion

```gherkin
Feature: RendirEvaluacion prellena y navega sobre una pregunta ya respondida (US-ADJ-12)

  Scenario: EvaluacionResponse expone el contenido de una respuesta ya confirmada
    Given una Evaluacion con una Respuesta confirmada para la pregunta 1 (contenido {opcion_indice: 0})
    When se construye el EvaluacionResponse (cualquiera de los 4 endpoints)
    Then incluye el contenido {opcion_indice: 0} asociado a la pregunta 1
    And no incluye es_correcta

  Scenario: El Estudiante vuelve a una pregunta ya respondida y ve su elección
    Given el Estudiante respondió la pregunta 1 y avanzó a la pregunta 2
    When vuelve a la pregunta 1 con "Anterior"
    Then ve marcada la misma opción que había confirmado
    And los inputs están deshabilitados

  Scenario: El botón navega sin reintentar registrar la respuesta
    Given el Estudiante está sobre una pregunta ya respondida, no la última
    When toca el botón
    Then avanza a la siguiente pregunta
    And no se llama a POST /evaluaciones/{id}/respuestas

  Scenario: El botón finaliza si la pregunta ya respondida es la última
    Given el Estudiante está sobre la última pregunta, ya respondida
    When toca el botón
    Then se llama a POST /evaluaciones/{id}/finalizar
    And navega a la revisión
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — reutiliza `respuesta_vigente_de`, ya existente; sin cambios de contrato que rompan
      compatibilidad (campo nuevo, aditivo).

**Capa(s) afectadas:**
- [x] Backend — `src/actividad_evaluativa/frameworks/api/schemas.py`,
      `src/actividad_evaluativa/frameworks/api/evaluaciones_router.py`
- [x] Frontend — `frontend/src/lib/actividad-evaluativa-api.ts`,
      `frontend/src/pages/RendirEvaluacion.tsx`

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/actividad_evaluativa/frameworks/api/schemas.py` | `RespuestaConfirmadaResponse` nuevo, campo `respuestas_confirmadas` en `EvaluacionResponse` |
| `src/actividad_evaluativa/frameworks/api/evaluaciones_router.py` | `_a_response` arma `respuestas_confirmadas` desde `evaluacion.respuesta_vigente_de(...)` |
| `tests/unit/inc3/test_evaluaciones_router_a_response.py` | tests nuevos del campo agregado |
| `frontend/src/lib/actividad-evaluativa-api.ts` | tipo + mapeo de `respuestas_confirmadas` |
| `frontend/src/pages/RendirEvaluacion.tsx` | prellenado de `seleccion`, inputs deshabilitados, botón navega sin reintentar sobre pregunta ya respondida |
| `frontend/src/pages/RendirEvaluacion.test.tsx` | tests nuevos del escenario |

---

## Referencias

- Relacionada con: `US-3.4.6` (pantalla original de rendir), `US-3.2.1`/`US-3.2.3` (Respuesta,
  `respuesta_vigente_de`)
- Detectada durante: revisión manual de Víctor,
  `quality/reports/uat/inc3/guion-manual-iteracion4.md` (pasos 8-9)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
