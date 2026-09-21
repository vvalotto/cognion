# US-6.2.7: Docente finaliza la sesión — ranking final

**Estado**: `Implementada` (2026-09-21)
**Iteracion / Sprint**: `INC-6.2`
**Tipo**: `feature backend`
**Agregado principal afectado**: `ActividadEvaluativaEnVivo`
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **dar por terminada la sesión y que todos vean el ranking final**,
para **cerrar la dinámica con el resultado de la clase**.

---

## Contexto del dominio

### Problema

Último paso del ciclo (§12). Transiciona la sesión a `Finalizada`, que es el estado que
`UnirseASesionEnVivo` ya usa para rechazar nuevas uniones (`US-6.1.3`, `SesionYaFinalizada`) y el
que hasta ahora los tests solo **sembraban** como evento. Con esta US `SesionEnVivoFinalizada` se
produce por API y esa siembra puede reemplazarse por el endpoint real.

Es también el momento en que el **Estudiante ve el ranking completo** por primera vez (§17 punto
10): durante la sesión solo ve su feedback personal.

### Decisión de spec (confirmada por Víctor 2026-09-21)

El modelo (§12) dice "tras cerrar la última pregunta", pero la tabla de excepciones (§13) **no**
incluye ninguna restricción de "quedan preguntas". Se especifica **sin** esa restricción: el
Docente puede finalizar **antes de agotar el set**, siempre que la pregunta actual esté cerrada
(INV-AEV-03) — cubre el caso de terminar la clase antes de tiempo. Víctor confirmó
esta opción el 2026-09-21: finalizar antes, sin restricción de última pregunta.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Comando | `FinalizarSesionEnVivo(sesion_id)` | Sin parámetros adicionales |
| Evento | `SesionEnVivoFinalizada` | Payload: `sesion_id`, `ocurrido_en` — el ranking final vive en el read model, no en el evento |
| Aggregate (ampliado) | `ActividadEvaluativaEnVivo` | `finalizar()` → `estado = Finalizada`; ya lo aplica `reconstruir()` (`US-6.1.3`) |
| Use Case (nuevo) | `FinalizarSesionEnVivoUseCase` | Valida, transiciona, `append`, lee el ranking final, publica |
| Endpoint (nuevo) | `POST /sesiones-en-vivo/{sesion_id}/finalizar` | Rol `docente` |

Broadcast a **todos** los conectados:
`{"tipo": "sesion_finalizada", "ranking": [{"posicion", "estudiante_id", "puntaje_acumulado"}]}`.

---

## Especificacion del comportamiento

### Precondicion

- Sesión `EnCurso` con la pregunta actual cerrada.
- `US-6.2.5` cerrada.

### Postcondicion

- `estado = Finalizada`; `SesionEnVivoFinalizada` persistida.
- Broadcast del ranking final **después** de persistir.
- Respuesta HTTP `200` con el estado actualizado.
- Un `UnirseASesionEnVivo` posterior se rechaza con `SesionYaFinalizada` (`US-6.1.3`); un
  `IniciarSesionEnVivo` con `SesionYaIniciada` (`US-6.1.4`).

### Invariantes

| ID | Invariante |
|----|------------|
| INV-AEV-03 | `FinalizarSesionEnVivo` requiere `pregunta_actual_cerrada = true` (`PreguntaActualNoCerrada`) |

### Excepciones

| Excepción | Condición | HTTP |
|---|---|---|
| `SesionNoExiste` | sin stream | 404 |
| `SesionYaFinalizada` | ya estaba `Finalizada` (error ya existente, `US-6.1.3`) | 422 |
| `SesionNoEnCurso` | está `EnEspera` (nunca se inició) | 422 |
| `PreguntaActualNoCerrada` | INV-AEV-03 | 422 |

Dos finalizaciones concurrentes: la segunda choca con el chequeo optimista y se traduce a
`SesionYaFinalizada`.

---

## Criterios de aceptacion

```gherkin
Feature: Docente finaliza la sesión en vivo (US-6.2.7)

  Scenario: Finalización exitosa tras cerrar la última pregunta
    Given una sesión en la última pregunta, ya cerrada
    When el Docente finaliza la sesión
    Then el estado pasa a Finalizada
    And todos los conectados reciben el ranking final ordenado por puntaje

  Scenario: Finalización anticipada con preguntas sin presentar
    Given una sesión en la pregunta 2 de 5, ya cerrada
    When el Docente finaliza la sesión
    Then se acepta y la sesión queda Finalizada

  Scenario: Después de finalizar no se puede unir nadie
    Given una sesión Finalizada
    When un Estudiante intenta unirse
    Then el sistema rechaza con SesionYaFinalizada (422)

  Scenario: Rechazo si la pregunta actual no fue cerrada
    Given una pregunta actual sin cerrar
    When el Docente intenta finalizar
    Then el sistema rechaza con PreguntaActualNoCerrada (422)

  Scenario: Rechazo si la sesión nunca se inició
    Given una sesión EnEspera
    When el Docente intenta finalizar
    Then el sistema rechaza con SesionNoEnCurso (422)

  Scenario: Rechazo si ya estaba finalizada
    Given una sesión Finalizada
    When el Docente intenta finalizar de nuevo
    Then el sistema rechaza con SesionYaFinalizada (422) sin emitir otro evento

  Scenario: Sesión inexistente
    Given un sesion_id que no corresponde a ninguna sesión
    When el Docente intenta finalizar
    Then el sistema rechaza con SesionNoExiste (404)

  Scenario: Rechazo por rol
    Given un usuario autenticado con rol Estudiante
    When intenta finalizar la sesión
    Then el sistema responde 403
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — transición de estado, mismo patrón que `US-6.1.4`.

**Capa(s) afectadas:**
- [x] Entities — `finalizar()`, `SesionEnVivoFinalizada`
- [x] Use Cases — `FinalizarSesionEnVivoUseCase`
- [x] Interface Adapters — método en el controller (vigilar CBO)
- [x] Frameworks — endpoint y wiring
- [ ] Frontend — diferido

**Limpieza de tests previos:** los tests de `US-6.1.3` y `US-6.1.4` que **siembran**
`SesionEnVivoFinalizada` (`_helpers.sembrar_evento_de_sesion`) pasan a usar el endpoint real y el
helper de siembra se elimina o queda solo para casos que no puedan producirse por API.

---

## Fuente de verdad UX

No aplica — backend puro. Resultado final del Estudiante y de la proyección en
`docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md`, pendiente de frontend.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/actividad_evaluativa/entities/actividad_evaluativa_en_vivo.py` | `finalizar()` |
| `src/actividad_evaluativa/entities/eventos_en_vivo.py` | `SesionEnVivoFinalizada` |
| `src/actividad_evaluativa/use_cases/finalizar_sesion_en_vivo.py` | `FinalizarSesionEnVivoUseCase` |
| `src/actividad_evaluativa/interface_adapters/controllers/`, `frameworks/api/`, `dependencies.py` | Método, endpoint, wiring |
| `tests/integration/inc6/_helpers.py`, tests de `US-6.1.3`/`6.1.4` | Reemplazar la siembra de `Finalizada` por el endpoint real |
| `tests/unit/inc6/`, `tests/integration/inc6/`, `tests/features/inc6/US-6.2.7*.feature` + step defs | Unitarios, HTTP + WebSocket, BDD |

---

## Referencias

- Modelo: `docs/design/domain/BC-actividad-evaluativa-modelo.md` §12, §13, §14 (INV-AEV-03), §16, §17 puntos 4 y 10
- Depende de: `US-6.2.5` (y `US-6.2.6` para el caso de la última pregunta)
- Consumida por: `US-6.2.8`, `US-6.2.9`
- Candidatas: `docs/plans/inc6/inc6-candidatas.md`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
