# US-6.2.6: Docente avanza a la siguiente pregunta

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-6.2`
**Tipo**: `feature backend`
**Agregado principal afectado**: `ActividadEvaluativaEnVivo`
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **pasar a la siguiente pregunta cuando terminé de comentar la anterior**,
para **controlar el ritmo de la clase, con una pausa deliberada entre pregunta y pregunta**.

---

## Contexto del dominio

### Problema

Cuarto paso del ciclo por pregunta (§12) y segundo del "avance en dos pasos" confirmado con Víctor
(§17 punto 4: `CerrarPreguntaActual` + `AvanzarSiguientePregunta`, descartado un único
`CerrarYAvanzar`). Deja la sesión en el mismo estado inicial que `US-6.1.4`: **solo el enunciado**
de la nueva pregunta, opciones ocultas hasta el próximo `MostrarOpcionesDeLaPregunta`.

Reutiliza el armado del mensaje `pregunta_presentada` de `US-6.1.4` (extraerlo a una función
compartida, no duplicarlo).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Comando | `AvanzarSiguientePregunta(sesion_id)` | Sin parámetros adicionales |
| Evento | `SiguientePreguntaPresentada` | Mismo shape que `SesionEnVivoIniciada`: `sesion_id`, `pregunta_actual_indice`, `pregunta: {pregunta_id, enunciado, tipo}`, `ocurrido_en` (sin opciones) |
| Aggregate (ampliado) | `ActividadEvaluativaEnVivo` | `avanzar()` → `pregunta_actual_indice += 1`, `opciones_mostradas = False`, `opciones_mostradas_en = None`, `pregunta_actual_cerrada = False`; `reconstruir()` aplica el evento |
| Use Case (nuevo) | `AvanzarSiguientePreguntaUseCase` | Valida, transiciona, obtiene el enunciado, `append`, publica |
| Endpoint (nuevo) | `POST /sesiones-en-vivo/{sesion_id}/avanzar` | Rol `docente` |

Broadcast a **todos** los conectados: `{"tipo": "pregunta_presentada", "pregunta_actual_indice": N,
"pregunta": {...}}` — el mismo mensaje que el inicio, para que el cliente no distinga entre "primera"
y "siguiente".

---

## Especificacion del comportamiento

### Precondicion

- Sesión `EnCurso` con la pregunta actual **cerrada** y con al menos una pregunta más en el set.
- `US-6.2.5` cerrada.

### Postcondicion

- `pregunta_actual_indice` avanza una posición; `opciones_mostradas`, `opciones_mostradas_en` y
  `pregunta_actual_cerrada` vuelven a su estado inicial.
- `SiguientePreguntaPresentada` persistida; broadcast del enunciado **después** de persistir.
- Respuesta HTTP `200` con el estado actualizado.

### Invariantes

| ID | Invariante |
|----|------------|
| INV-AEV-03 | `AvanzarSiguientePregunta` requiere `pregunta_actual_cerrada = true` (`PreguntaActualNoCerrada`) |

### Excepciones

| Excepción | Condición | HTTP |
|---|---|---|
| `SesionNoExiste` | sin stream | 404 |
| `SesionNoEnCurso` | `EnEspera` o `Finalizada` | 422 |
| `PreguntaActualNoCerrada` (nueva) | INV-AEV-03 | 422 |
| `NoQuedanPreguntas` (nueva) | la pregunta actual es la última — el Docente debe finalizar | 422 |

Dos avances concurrentes: el segundo choca con el chequeo optimista y se traduce a
`PreguntaActualNoCerrada` (el primero ya dejó la pregunta nueva sin cerrar).

---

## Criterios de aceptacion

```gherkin
Feature: Docente avanza a la siguiente pregunta (US-6.2.6)

  Scenario: Avance exitoso
    Given una sesión en la pregunta 1 de 5, ya cerrada
    When el Docente avanza
    Then pregunta_actual_indice pasa a 1 con las opciones ocultas y la pregunta sin cerrar
    And todos los conectados reciben el enunciado de la pregunta 2, sin opciones

  Scenario: Avance hasta la penúltima pregunta
    Given una sesión en la pregunta 4 de 5, ya cerrada
    When el Docente avanza
    Then queda en la pregunta 5

  Scenario: Rechazo si la pregunta actual no fue cerrada
    Given una pregunta con las opciones mostradas y sin cerrar
    When el Docente intenta avanzar
    Then el sistema rechaza con PreguntaActualNoCerrada (422)

  Scenario: Rechazo en la última pregunta
    Given una sesión en la última pregunta, ya cerrada
    When el Docente intenta avanzar
    Then el sistema rechaza con NoQuedanPreguntas (422)

  Scenario: Rechazo si la sesión no está en curso
    Given una sesión EnEspera o Finalizada
    When el Docente intenta avanzar
    Then el sistema rechaza con SesionNoEnCurso (422)

  Scenario: Sesión inexistente
    Given un sesion_id que no corresponde a ninguna sesión
    When el Docente intenta avanzar
    Then el sistema rechaza con SesionNoExiste (404)

  Scenario: Rechazo por rol
    Given un usuario autenticado con rol Estudiante
    When intenta avanzar
    Then el sistema responde 403
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — transición de estado, mismo patrón que `US-6.1.4`.

**Capa(s) afectadas:**
- [x] Entities — `avanzar()`, `SiguientePreguntaPresentada`, `PreguntaActualNoCerrada`, `NoQuedanPreguntas`
- [x] Use Cases — `AvanzarSiguientePreguntaUseCase`
- [x] Interface Adapters — método en el controller (vigilar CBO)
- [x] Frameworks — endpoint y wiring
- [ ] Frontend — diferido

---

## Fuente de verdad UX

No aplica — backend puro. Pantalla de control del Docente en
`docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md`, pendiente de frontend.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/actividad_evaluativa/entities/actividad_evaluativa_en_vivo.py` | `avanzar()`, `reconstruir()` |
| `src/actividad_evaluativa/entities/eventos_en_vivo.py` | `SiguientePreguntaPresentada` |
| `src/actividad_evaluativa/entities/errors.py` | `PreguntaActualNoCerrada`, `NoQuedanPreguntas` |
| `src/actividad_evaluativa/use_cases/avanzar_siguiente_pregunta.py` | `AvanzarSiguientePreguntaUseCase` |
| `src/actividad_evaluativa/use_cases/iniciar_sesion_en_vivo.py` | Extraer el armado del mensaje `pregunta_presentada` a una función compartida |
| `src/actividad_evaluativa/interface_adapters/controllers/`, `frameworks/api/`, `dependencies.py` | Método, endpoint, wiring |
| `tests/unit/inc6/`, `tests/integration/inc6/`, `tests/features/inc6/US-6.2.6*.feature` + step defs | Unitarios, HTTP + WebSocket, BDD |

---

## Referencias

- Modelo: `docs/design/domain/BC-actividad-evaluativa-modelo.md` §12, §13, §14 (INV-AEV-03), §16, §17 punto 4
- Precedente: `US-6.1.4` (presentar el enunciado)
- Depende de: `US-6.2.5`
- Consumida por: `US-6.2.7`, `US-6.2.9`
- Candidatas: `docs/plans/inc6/inc6-candidatas.md`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
