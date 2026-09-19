# US-6.2.5: Docente cierra la pregunta actual — respuesta correcta, histograma y ranking

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-6.2`
**Tipo**: `feature backend`
**Agregado principal afectado**: `ActividadEvaluativaEnVivo`
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **cerrar la pregunta cuando quiero y que en la proyección aparezcan la respuesta correcta,
cuántos eligieron cada opción y el ranking**,
para **comentar el resultado en el aula antes de pasar a la siguiente**.

---

## Contexto del dominio

### Problema

Es el momento crítico de RF-09 y el del **RNF de rendimiento**: al cerrar, el servidor debe armar
y transmitir el resultado a hasta 60 conectados en **≤ 100 ms** de procesamiento (`RNF_v1.md`,
Rendimiento, Escenario 1). Por eso no calcula nada pesado: **lee** los read models de `US-6.2.3`
(ranking e histograma ya acumulados) y la respuesta correcta de la pregunta, persiste un evento
mínimo y publica **un único mensaje**.

El cierre es **manual** (tercero de los tres pasos manuales del Docente, §12). No hay disparo
automático por tiempo: el corte de aceptación por estudiante (`TiempoAgotado`) es independiente de
que el Docente haya cerrado.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Comando | `CerrarPreguntaActual(sesion_id)` | Sin parámetros adicionales |
| Evento | `PreguntaEnVivoCerrada` | Payload mínimo: `sesion_id`, `pregunta_actual_indice`, `pregunta_id`, `ocurrido_en` — el ranking y el histograma **no** se persisten en el evento, viven en los read models |
| Aggregate (ampliado) | `ActividadEvaluativaEnVivo` | `cerrar_pregunta()` → `pregunta_actual_cerrada = True`; `reconstruir()` aplica el evento |
| Use Case (nuevo) | `CerrarPreguntaActualUseCase` | Valida, transiciona, `append`, lee proyecciones y respuesta correcta, publica un único mensaje |
| Endpoint (nuevo) | `POST /sesiones-en-vivo/{sesion_id}/cerrar-pregunta` | Rol `docente` |

**Mensaje de broadcast** (§16, tercera fila), un único payload a **todos** los conectados:

```json
{"tipo": "pregunta_cerrada",
 "pregunta_actual_indice": N,
 "respuesta_correcta": {"contenido": {"opcion_indice": 2}, "texto": "...", "opciones": ["..."]},
 "distribucion": [{"opcion": "0", "cantidad": 12}, {"opcion": "2", "cantidad": 40}],
 "ranking": [{"posicion": 1, "estudiante_id": "...", "puntaje_acumulado": 3200}]}
```

La secuencia histograma → ranking es **solo de presentación** (temporizador local del cliente de
proyección, sin round-trip): el servidor manda todo junto.

**Nota — nombres en el ranking:** el ranking contiene solo `estudiante_id`, igual que la sala de
espera de `US-6.1.3`. Resolver nombres requiere un puerto nuevo hacia Identidad y es alcance de la
iteración de frontend (ver ítem abierto en `inc6-candidatas.md`).

---

## Especificacion del comportamiento

### Precondicion

- Sesión `EnCurso`, con las opciones de la pregunta actual mostradas y sin cerrar.
- `US-6.2.2` y `US-6.2.3` cerradas.

### Postcondicion

- `pregunta_actual_cerrada = True`; `PreguntaEnVivoCerrada` persistida en el stream de la sesión.
- Broadcast del mensaje `pregunta_cerrada` **después** de persistir.
- Respuesta HTTP `200` con el estado actualizado de la sesión.
- Desde este momento `ResponderPreguntaEnVivo` se rechaza con `PreguntaYaCerrada` (`US-6.2.4`).

### Invariantes

| ID | Invariante |
|----|------------|
| INV-AEV-09 (parte) | `CerrarPreguntaActual` requiere `opciones_mostradas = True` (`OpcionesNoMostradasTodavia`) |
| — | Cerrar una pregunta ya cerrada se rechaza (`PreguntaYaCerrada`) sin reemitir el evento |

### Excepciones

| Excepción | Condición | HTTP |
|---|---|---|
| `SesionNoExiste` | sin stream | 404 |
| `SesionNoEnCurso` | `EnEspera` o `Finalizada` | 422 |
| `OpcionesNoMostradasTodavia` | `opciones_mostradas = False` | 422 |
| `PreguntaYaCerrada` | ya estaba cerrada | 422 |

---

## Criterios de aceptacion

```gherkin
Feature: Docente cierra la pregunta actual (US-6.2.5)

  Scenario: Cierre exitoso
    Given una pregunta con las opciones mostradas y varios Estudiantes que respondieron
    When el Docente cierra la pregunta
    Then pregunta_actual_cerrada pasa a verdadero y se persiste PreguntaEnVivoCerrada
    And todos los conectados reciben un único mensaje con la respuesta correcta, el histograma y el ranking
    And la respuesta HTTP es 200

  Scenario: El ranking del mensaje refleja los puntajes acumulados
    Given tres Estudiantes con distintos puntajes acumulados
    When el Docente cierra la pregunta
    Then el ranking viene ordenado por puntaje descendente con su posición

  Scenario: El histograma cuenta las respuestas por opción
    Given 5 respuestas a la opción "0" y 3 a la opción "2"
    When el Docente cierra la pregunta
    Then la distribución informa 5 para "0" y 3 para "2"

  Scenario: Cerrar sin ninguna respuesta
    Given una pregunta con las opciones mostradas y ninguna respuesta
    When el Docente la cierra
    Then se acepta, con distribución vacía y el ranking con todos en su puntaje actual

  Scenario: Rechazo si las opciones no se mostraron
    Given una pregunta con solo el enunciado presentado
    When el Docente intenta cerrarla
    Then el sistema rechaza con OpcionesNoMostradasTodavia (422)

  Scenario: Rechazo si ya estaba cerrada
    Given una pregunta ya cerrada
    When el Docente intenta cerrarla de nuevo
    Then el sistema rechaza con PreguntaYaCerrada (422) sin emitir otro evento

  Scenario: Rechazo si la sesión no está en curso
    Given una sesión EnEspera
    When el Docente intenta cerrar la pregunta
    Then el sistema rechaza con SesionNoEnCurso (422)

  Scenario: Sesión inexistente
    Given un sesion_id que no corresponde a ninguna sesión
    When el Docente intenta cerrar la pregunta
    Then el sistema rechaza con SesionNoExiste (404)

  Scenario: Rechazo por rol
    Given un usuario autenticado con rol Estudiante
    When intenta cerrar la pregunta
    Then el sistema responde 403
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — transición de estado más lectura de proyecciones ya construidas. La medición formal del
  RNF se hace en `US-6.2.9`; esta US solo debe **no agregar trabajo pesado** en el camino del cierre.

**Capa(s) afectadas:**
- [x] Entities — `cerrar_pregunta()`, `PreguntaEnVivoCerrada`, `PreguntaYaCerrada`
- [x] Use Cases — `CerrarPreguntaActualUseCase` (vigilar CBO: event store, proyecciones (lectura),
  `PreguntaConsultaPort`, canal)
- [x] Interface Adapters — método en el controller (mismo criterio de separar si se acerca al umbral)
- [x] Frameworks — endpoint y wiring
- [ ] Frontend — diferido

---

## Fuente de verdad UX

No aplica — backend puro. Proyección del resultado (histograma → ranking) en
`docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md` §2.4, pendiente de frontend.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/actividad_evaluativa/entities/actividad_evaluativa_en_vivo.py` | `cerrar_pregunta()`, `reconstruir()` |
| `src/actividad_evaluativa/entities/eventos_en_vivo.py` | `PreguntaEnVivoCerrada` |
| `src/actividad_evaluativa/entities/errors.py` | `PreguntaYaCerrada` (si no la creó `US-6.2.4`) |
| `src/actividad_evaluativa/use_cases/cerrar_pregunta_actual.py` | `CerrarPreguntaActualUseCase` |
| `src/actividad_evaluativa/interface_adapters/controllers/`, `frameworks/api/`, `dependencies.py` | Método, endpoint, wiring |
| `tests/unit/inc6/`, `tests/integration/inc6/`, `tests/features/inc6/US-6.2.5*.feature` + step defs | Incluye el mensaje completo a dos WebSockets |

---

## Referencias

- Modelo: `docs/design/domain/BC-actividad-evaluativa-modelo.md` §12, §13, §15, §16, §17 punto 4
- RNF: `docs/rf/RNF_v1.md` Rendimiento, Escenario 1
- Depende de: `US-6.2.2`, `US-6.2.3`, `US-6.2.4`
- Consumida por: `US-6.2.6`, `US-6.2.7`, `US-6.2.9`
- Candidatas: `docs/plans/inc6/inc6-candidatas.md`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
