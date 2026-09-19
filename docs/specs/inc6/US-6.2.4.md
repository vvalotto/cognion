# US-6.2.4: Estudiante responde una pregunta en vivo

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-6.2`
**Tipo**: `feature backend`
**Agregado principal afectado**: `ParticipacionEnVivo`
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Estudiante**,
quiero **responder la pregunta tocando una opción y ver al instante si acerté y cuántos puntos
llevo**,
para **saber cómo voy sin esperar a que el Docente cierre la pregunta**.

---

## Contexto del dominio

### Problema

Núcleo de RF-09/RF-10. Cada respuesta es un comando sobre **su** `ParticipacionEnVivo` (un stream
por alumno, sin contención entre alumnos). El sistema mide `tiempo_respuesta` **en el servidor**
desde `OpcionesEnVivoMostradas` (`US-6.2.2`), corrige (`PreguntaConsultaPort.evaluar_correccion`),
calcula el puntaje (`US-6.2.1`) y actualiza las proyecciones (`US-6.2.3`) — todo en una única
transacción. **Un solo intento por pregunta** (INV-AEV-07, estilo Kahoot).

Decisión de UX ya tomada (`US-6.0.2`, §17 puntos 9–10): tocar la tarjeta responde de inmediato, y
el Estudiante recibe **feedback personal** (acierto, puntos y acumulado) pero **no** el ranking,
que queda para el resultado final.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Comando | `ResponderPreguntaEnVivo(sesion_id, estudiante_id, pregunta_id, respuesta)` | `estudiante_id` sale del JWT; `respuesta` = `contenido` con el mismo shape que `Respuesta.contenido` (`{opcion_indice}` o `{valor}`) |
| VO (nuevo) | `RespuestaEnVivo` | `pregunta_id`, `contenido`, `es_correcta`, `tiempo_respuesta_segundos`, `puntaje` — inmutable (§14) |
| Evento | `RespuestaEnVivoRegistrada` | Payload: `sesion_id`, `estudiante_id`, `pregunta_id`, `contenido`, `es_correcta`, `tiempo_respuesta_segundos`, `puntaje`, `ocurrido_en` |
| Aggregate (ampliado) | `ParticipacionEnVivo` | `respuestas: list[RespuestaEnVivo]`, `responder(...)`, `puntaje_acumulado`, `reconstruir()` aplica el evento |
| Use Case (nuevo) | `ResponderPreguntaEnVivoUseCase` | Orquesta las validaciones, corrección, puntaje, proyecciones, `append` y broadcast del conteo |
| Endpoint (nuevo) | `POST /sesiones-en-vivo/{sesion_id}/responder` | Rol `estudiante`; body `{pregunta_id, contenido}` |

**Respuesta HTTP `200`** (feedback personal, sin ranking): `{es_correcta, puntaje, puntaje_acumulado}`.

**Broadcast del conteo** (§16, opciones): tras registrar, a **todos** los conectados:
`{"tipo": "conteo_respuestas_actualizado", "pregunta_actual_indice": N, "cantidad_respuestas": M}`
— total recibido, **sin desglose por opción** (evita el efecto "todos eligen lo que va ganando").
`M` sale de `ProyeccionesEnVivoQueryPort.cantidad_respuestas` (`US-6.2.3`).

---

## Especificacion del comportamiento

### Precondicion

- `US-6.2.1`, `US-6.2.2` y `US-6.2.3` cerradas.
- El Estudiante se unió a la sesión (`US-6.1.3`).

### Postcondicion

- `RespuestaEnVivoRegistrada` persistida como evento del stream de la participación, **junto con**
  la actualización de `ranking_por_sesion` y `distribucion_por_pregunta` (mismo `commit`, contrato
  de `US-6.2.3`).
- `tiempo_respuesta_segundos = ahora(servidor) − opciones_mostradas_en`; nunca lo envía el cliente.
- `puntaje` calculado con `calcular_puntaje` (0 si es incorrecta).
- Broadcast del conteo total después de persistir (best-effort).

### Invariantes

| ID | Invariante |
|----|------------|
| INV-AEV-07 | A lo sumo una `RespuestaEnVivo` por `pregunta_id` en la participación (un solo intento) |
| INV-AEV-08 | Se rechaza con `TiempoAgotado` si `tiempo_respuesta > tiempo_limite_por_pregunta_segundos`, aunque el Docente aún no haya cerrado la pregunta |
| INV-AEV-09 (parte) | No se puede responder antes de que el Docente muestre las opciones (`OpcionesNoMostradasTodavia`) |

### Excepciones

| Excepción | Condición | HTTP |
|---|---|---|
| `SesionNoExiste` | sin stream | 404 |
| `ParticipacionNoExiste` (nueva) | el Estudiante no se unió a la sesión | 404 |
| `SesionNoEnCurso` | `EnEspera` o `Finalizada` | 422 |
| `PreguntaNoActual` (nueva) | `pregunta_id` no es la pregunta actual | 422 |
| `OpcionesNoMostradasTodavia` (nueva) | `opciones_mostradas = False` | 422 |
| `PreguntaYaCerrada` (nueva) | el Docente ya cerró la pregunta actual | 422 |
| `TiempoAgotado` (nueva) | INV-AEV-08 | 422 |
| `RespuestaYaRegistrada` (nueva) | INV-AEV-07, incluido el doble envío por reintento de red | 422 |

Un doble envío concurrente resuelve por el chequeo optimista del stream de la participación
(`ConcurrenciaOptimistaError` → `RespuestaYaRegistrada`), igual que `US-6.1.4` con `SesionYaIniciada`.

---

## Criterios de aceptacion

```gherkin
Feature: Estudiante responde una pregunta en vivo (US-6.2.4)

  Scenario: Respuesta correcta a tiempo
    Given una pregunta con las opciones mostradas y un Estudiante unido
    When el Estudiante elige la opción correcta dentro del tiempo límite
    Then se registra la respuesta con tiempo_respuesta medido por el servidor
    And la respuesta HTTP trae es_correcta=true, el puntaje de esa pregunta y el puntaje acumulado
    And todos los conectados reciben el conteo actualizado de respuestas, sin desglose por opción

  Scenario: Respuesta incorrecta
    Given una pregunta con las opciones mostradas
    When el Estudiante elige una opción incorrecta
    Then se registra la respuesta con puntaje 0 y es_correcta=false

  Scenario: Las proyecciones se actualizan junto con el evento
    Given un Estudiante que responde una pregunta
    When se registra la respuesta
    Then su puntaje acumulado en el ranking y el histograma de esa opción reflejan la respuesta

  Scenario: Un solo intento por pregunta
    Given un Estudiante que ya respondió la pregunta actual
    When intenta responderla de nuevo
    Then el sistema rechaza con RespuestaYaRegistrada (422) y no cambia su puntaje

  Scenario: Rechazo por tiempo agotado
    Given una pregunta cuyas opciones se mostraron hace más del tiempo límite
    When el Estudiante intenta responder
    Then el sistema rechaza con TiempoAgotado (422)

  Scenario: Rechazo antes de que se muestren las opciones
    Given una pregunta con solo el enunciado presentado
    When el Estudiante intenta responder
    Then el sistema rechaza con OpcionesNoMostradasTodavia (422)

  Scenario: Rechazo si la pregunta ya fue cerrada
    Given una pregunta cerrada por el Docente
    When el Estudiante intenta responder
    Then el sistema rechaza con PreguntaYaCerrada (422)

  Scenario: Rechazo si no es la pregunta actual
    Given una sesión en la pregunta 2
    When el Estudiante responde con el pregunta_id de la pregunta 1
    Then el sistema rechaza con PreguntaNoActual (422)

  Scenario: Estudiante que no se unió
    Given un Estudiante que nunca se unió a la sesión
    When intenta responder
    Then el sistema rechaza con ParticipacionNoExiste (404)

  Scenario: Doble envío simultáneo
    Given dos envíos simultáneos de la misma respuesta del mismo Estudiante
    When se procesan
    Then uno se registra y el otro recibe RespuestaYaRegistrada (422)

  Scenario: Rechazo por rol
    Given un usuario autenticado con rol Docente
    When intenta responder
    Then el sistema responde 403
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — sigue el patrón de `Evaluacion` (`RegistrarRespuesta`, `US-3.2.1`) con las variantes del
  modo en vivo (un intento, tiempo medido contra `OpcionesEnVivoMostradas`) y el contrato de
  atomicidad ya fijado en `US-6.2.3`.

**Capa(s) afectadas:**
- [x] Entities — `RespuestaEnVivo`, `RespuestaEnVivoRegistrada`, `ParticipacionEnVivo.responder()`,
  errores nuevos
- [x] Use Cases — `ResponderPreguntaEnVivoUseCase` (**dependencias: sesión (event store),
  `PreguntaConsultaPort`, proyecciones escritura/lectura, canal — vigilar CBO en Fase 2**)
- [x] Interface Adapters — método `responder` en el controller (**evaluar un controller propio
  para las respuestas: el actual llega a 4–5 use cases**)
- [x] Frameworks — endpoint y wiring
- [ ] Frontend — diferido

---

## Fuente de verdad UX

No aplica — backend puro. Pantalla del celular del Estudiante (tarjetas táctiles, feedback
inmediato) en `docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md`, pendiente de frontend.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/actividad_evaluativa/entities/participacion_en_vivo.py` | `RespuestaEnVivo`, `responder()`, `puntaje_acumulado`, `reconstruir()` |
| `src/actividad_evaluativa/entities/eventos_en_vivo.py` | `RespuestaEnVivoRegistrada` |
| `src/actividad_evaluativa/entities/errors.py` | Errores nuevos de la tabla |
| `src/actividad_evaluativa/use_cases/responder_pregunta_en_vivo.py` | `ResponderPreguntaEnVivoUseCase` |
| `src/actividad_evaluativa/interface_adapters/controllers/` | Método/controller |
| `src/actividad_evaluativa/frameworks/api/` | `POST .../responder`, schemas, wiring |
| `tests/unit/inc6/`, `tests/integration/inc6/`, `tests/features/inc6/US-6.2.4*.feature` + step defs | Incluye **concurrencia real** (60 respuestas simultáneas y doble envío) contra la DB |

---

## Referencias

- Modelo: `docs/design/domain/BC-actividad-evaluativa-modelo.md` §12, §13 (resultado devuelto), §14 (INV-AEV-07/08/09), §15, §16, §17 puntos 3, 9, 10
- Precedente: `US-3.2.1` (`RegistrarRespuesta`), `US-6.1.4` (traducción de `ConcurrenciaOptimistaError`)
- Depende de: `US-6.2.1`, `US-6.2.2`, `US-6.2.3`
- Consumida por: `US-6.2.5`
- Candidatas: `docs/plans/inc6/inc6-candidatas.md`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
