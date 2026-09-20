# US-6.2.2: Docente muestra las opciones de la pregunta actual

**Estado**: `Implementada`
**Iteracion / Sprint**: `INC-6.2`
**Tipo**: `feature backend`
**Agregado principal afectado**: `ActividadEvaluativaEnVivo`
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **revelar las opciones de la pregunta cuando ya leí el enunciado en voz alta**,
para **decidir yo cuándo arranca el temporizador y todos empiezan a responder al mismo tiempo**.

---

## Contexto del dominio

### Problema

Segundo paso manual de cada pregunta (`BC-actividad-evaluativa-modelo.md` §12, §17 punto 7):
`SesionEnVivoIniciada` (`US-6.1.4`) presenta solo el enunciado; recién `MostrarOpcionesDeLaPregunta`
revela las opciones y **arranca el temporizador**. El instante de `OpcionesEnVivoMostradas` es la
referencia real de `tiempo_respuesta` (INV-AEV-08) — no el de presentar el enunciado.

Por eso el aggregate necesita recordar **cuándo** se mostraron las opciones
(`opciones_mostradas_en`), y `reconstruir()` debe aplicar el evento nuevo.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Comando | `MostrarOpcionesDeLaPregunta(sesion_id)` | Sin parámetros adicionales |
| Evento | `OpcionesEnVivoMostradas` | Payload: `sesion_id`, `pregunta_actual_indice`, `pregunta_id`, `opciones` (lista de textos, o `null` para Verdadero/Falso), `ocurrido_en` — **sin** indicar la correcta |
| Aggregate (ampliado) | `ActividadEvaluativaEnVivo` | Campo nuevo `opciones_mostradas_en: datetime \| None`; método `mostrar_opciones(ahora)`; `reconstruir()` aplica el evento |
| Use Case (nuevo) | `MostrarOpcionesEnVivoUseCase` | Valida, transiciona, obtiene las opciones por `PreguntaConsultaPort.obtener_contenido`, hace `append` y publica |
| Endpoint (nuevo) | `POST /sesiones-en-vivo/{sesion_id}/mostrar-opciones` | Rol `docente` |

Mensaje de broadcast (§16, segunda fila): a **todos los conectados**:
`{"tipo": "opciones_mostradas", "pregunta_actual_indice": N, "opciones": [...] | null,
"tiempo_limite_por_pregunta_segundos": T, "cantidad_respuestas": 0}` — arranca el temporizador
visible; el conteo de respuestas lo mantiene `US-6.2.4`. Nunca incluye la opción correcta.

---

## Especificacion del comportamiento

### Precondicion

- Sesión `EnCurso` con una pregunta actual cuyas opciones **todavía no** se mostraron.
- `US-6.1.4` cerrada.

### Postcondicion

- `opciones_mostradas = True`, `opciones_mostradas_en = ocurrido_en` del evento.
- `OpcionesEnVivoMostradas` persistida en el stream de la sesión.
- Broadcast de las opciones (sin la correcta) a todos los conectados, **después** de persistir.
- Respuesta HTTP `200` con el estado actualizado de la sesión (`SesionEnVivoResponse`).

### Invariantes

| ID | Invariante |
|----|------------|
| INV-AEV-09 (parte) | `MostrarOpcionesDeLaPregunta` sobre una pregunta que ya las tiene mostradas se rechaza (`OpcionesYaMostradas`) y **no reemite** el evento |

### Excepciones

| Excepción | Condición |
|---|---|
| `SesionNoExiste` | `sesion_id` sin stream (404) |
| `SesionNoEnCurso` (nueva) | La sesión está `EnEspera` o `Finalizada` (422) |
| `OpcionesYaMostradas` (nueva) | Las opciones de la pregunta actual ya se mostraron (422) |

`SesionNoEnCurso` la reutilizan `US-6.2.4` a `US-6.2.7`.

---

## Criterios de aceptacion

```gherkin
Feature: Docente muestra las opciones de la pregunta actual (US-6.2.2)

  Scenario: Mostrar opciones de una pregunta de opción múltiple
    Given una sesión EnCurso con el enunciado de la primera pregunta presentado
    When el Docente muestra las opciones
    Then opciones_mostradas pasa a verdadero y queda registrado el instante
    And todos los conectados reciben las opciones sin indicar la correcta
    And la respuesta HTTP es 200

  Scenario: Mostrar opciones de una pregunta de Verdadero/Falso
    Given una sesión EnCurso cuya pregunta actual es de Verdadero/Falso
    When el Docente muestra las opciones
    Then el mensaje indica el tipo de pregunta y no trae lista de opciones

  Scenario: Rechazo si las opciones ya estaban mostradas
    Given una pregunta con las opciones ya mostradas
    When el Docente intenta mostrarlas de nuevo
    Then el sistema rechaza con OpcionesYaMostradas (422) sin emitir un evento nuevo

  Scenario: Rechazo si la sesión no está en curso
    Given una sesión en estado EnEspera
    When el Docente intenta mostrar las opciones
    Then el sistema rechaza con SesionNoEnCurso (422)

  Scenario: Sesión inexistente
    Given un sesion_id que no corresponde a ninguna sesión
    When el Docente intenta mostrar las opciones
    Then el sistema rechaza con SesionNoExiste (404)

  Scenario: Rechazo por rol
    Given un usuario autenticado con rol Estudiante
    When intenta mostrar las opciones
    Then el sistema responde 403
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — transición de estado sobre el aggregate ya construido, mismo patrón que `US-6.1.4`.

**Capa(s) afectadas:**
- [x] Entities — `mostrar_opciones()`, `opciones_mostradas_en`, `OpcionesEnVivoMostradas`,
  `SesionNoEnCurso`/`OpcionesYaMostradas`
- [x] Use Cases — `MostrarOpcionesEnVivoUseCase`
- [x] Interface Adapters — método `mostrar_opciones` en `SesionesEnVivoController` (**4° use
  case: verificar CBO en Fase 2 y, si llega al umbral, separar por responsabilidad** —
  `feedback_cbo_pre_push_no_fase7`)
- [x] Frameworks — endpoint y wiring
- [ ] Frontend — diferido, mismo criterio que la Iteración 1

---

## Fuente de verdad UX

No aplica a esta US — backend puro. Pantallas en
`docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md` (control del Docente, proyección,
celular del Estudiante), pendientes de iteración de frontend.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/actividad_evaluativa/entities/actividad_evaluativa_en_vivo.py` | `opciones_mostradas_en`, `mostrar_opciones()`, `reconstruir()` |
| `src/actividad_evaluativa/entities/eventos_en_vivo.py` | `OpcionesEnVivoMostradas` |
| `src/actividad_evaluativa/entities/errors.py` | `SesionNoEnCurso`, `OpcionesYaMostradas` |
| `src/actividad_evaluativa/use_cases/mostrar_opciones_en_vivo.py` | `MostrarOpcionesEnVivoUseCase` |
| `src/actividad_evaluativa/interface_adapters/controllers/sesiones_en_vivo_controller.py` | Método nuevo |
| `src/actividad_evaluativa/frameworks/api/sesiones_en_vivo_router.py` | `POST .../mostrar-opciones` (rol `docente`) |
| `src/actividad_evaluativa/frameworks/dependencies.py` | Wiring |
| `tests/unit/inc6/`, `tests/integration/inc6/`, `tests/features/inc6/US-6.2.2*.feature` + step defs | Unitarios, HTTP + WebSocket, BDD |

Al cambiar la firma del constructor del controller, **grepear antes** los tests que lo construyen.

---

## Referencias

- Modelo: `docs/design/domain/BC-actividad-evaluativa-modelo.md` §12, §13, §14 (INV-AEV-09), §16, §17 puntos 7–8
- Depende de: `US-6.1.4`
- Consumida por: `US-6.2.4` (`tiempo_respuesta` se mide desde `opciones_mostradas_en`)
- Candidatas: `docs/plans/inc6/inc6-candidatas.md`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
