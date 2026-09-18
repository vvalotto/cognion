# US-6.1.4: Docente inicia la sesión en vivo — se presenta la primera pregunta

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-6.1`
**Tipo**: `feature backend`
**Agregado principal afectado**: `ActividadEvaluativaEnVivo`
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **iniciar la sesión en vivo cuando ya se unieron los estudiantes que quiero esperar**,
para **arrancar la dinámica — todos los conectados ven al mismo tiempo el enunciado de la
primera pregunta**.

---

## Contexto del dominio

### Problema

Cierra la Iteración 1: transiciona `ActividadEvaluativaEnVivo` de `EnEspera` a `EnCurso` y
dispara el primer broadcast de contenido de pregunta (solo el **enunciado**, sin opciones — el
paso de revelar opciones es `MostrarOpcionesDeLaPregunta`, comando manual distinto, Iteración 2,
`BC-actividad-evaluativa-modelo.md` §12/§17 punto 7). Con esta US, el flujo completo de RF-08
(crear → unirse → iniciar) queda operable de punta a punta por WebSocket + HTTP, listo para que
la Iteración 2 agregue la dinámica pregunta por pregunta.

No hay disparo automático por tiempo: iniciar la sesión es siempre una decisión manual del
Docente (§12, "Tres momentos, los tres decisión manual del Docente").

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Comando | `IniciarSesionEnVivo(sesion_id)` | Sin parámetros adicionales — la sesión ya tiene todo lo necesario desde `SesionEnVivoCreada` |
| Evento | `SesionEnVivoIniciada` | Payload: `sesion_id`, `pregunta_actual_indice=0`, enunciado de la primera pregunta (`pregunta_id`, `enunciado`, `tipo`) — **sin** las opciones |
| Use Case (nuevo) | `IniciarSesionEnVivoUseCase` | Valida estado, transiciona el aggregate, hace `append`, publica por `CanalTiempoRealPort` el mensaje de "pregunta actual, solo enunciado" a todos los conectados al canal |
| Endpoint (nuevo) | `POST /sesiones-en-vivo/{sesion_id}/iniciar` | Rol `docente` |

Mensaje de broadcast (§16, primera fila de la tabla): "Solo el enunciado de la pregunta actual
— sin opciones todavía", dirigido a **todos los conectados** al canal `sesion_id` (Docente en
su vista de control, Estudiantes en su celular, proyección del aula si ya está conectada).

---

## Especificacion del comportamiento

### Precondicion

- `US-6.1.2` cerrada — existe la `ActividadEvaluativaEnVivo` en estado `EnEspera`.
- `US-6.1.1` cerrada — canal de broadcast disponible.
- No depende de que haya algún Estudiante unido todavía (`US-6.1.3`) — el Docente puede iniciar
  con cero participantes, aunque en la práctica no tendría sentido pedagógico; el dominio no lo
  impide, mismo criterio de no agregar una invariante sin pedido explícito de RF-08.

### Postcondicion

- `estado` pasa de `EnEspera` a `EnCurso`, `pregunta_actual_indice = 0`,
  `opciones_mostradas = False`, `pregunta_actual_cerrada = False`.
- `SesionEnVivoIniciada` persistida como segundo evento del stream de la sesión.
- Se publica por `CanalTiempoRealPort` el enunciado de la primera pregunta (sin opciones) a
  todos los conectados al canal `sesion_id`.
- Respuesta HTTP `200` con el estado actualizado de la sesión.
- Un segundo `IniciarSesionEnVivo` sobre la misma sesión se rechaza (`SesionYaIniciada`) — no
  hay caso de uso de "reiniciar" una sesión ya arrancada.

### Invariantes

No agrega invariantes nuevas de dominio — reutiliza las ya definidas en `US-6.1.2`
(INV-AEV-01/02, sin efecto sobre esta transición de estado).

### Excepciones

| Excepción | Condición |
|---|---|
| `SesionNoExiste` | `sesion_id` no corresponde a ninguna `ActividadEvaluativaEnVivo` (404) |
| `SesionYaIniciada` | La sesión ya está en `EnCurso` o `Finalizada` (422) |

---

## Criterios de aceptacion

```gherkin
Feature: Docente inicia la sesión en vivo (US-6.1.4)

  Scenario: Inicio exitoso
    Given una sesión en vivo en estado EnEspera con al menos un Estudiante unido
    When el Docente la inicia
    Then el estado pasa a EnCurso con pregunta_actual_indice=0
    And todos los conectados al canal reciben el enunciado de la primera pregunta, sin opciones

  Scenario: Inicio sin ningún Estudiante unido todavía
    Given una sesión en vivo en estado EnEspera sin ningún Estudiante unido
    When el Docente la inicia
    Then la operación se acepta igual — el dominio no exige un mínimo de participantes

  Scenario: Rechazo por sesión ya iniciada
    Given una sesión en vivo ya en estado EnCurso
    When el Docente intenta iniciarla de nuevo
    Then el sistema rechaza la operación con SesionYaIniciada (422)

  Scenario: Sesión inexistente
    Given un sesion_id que no corresponde a ninguna sesión en vivo
    When el Docente intenta iniciarla
    Then el sistema rechaza la operación con SesionNoExiste (404)

  Scenario: Rechazo por rol
    Given un usuario autenticado con rol Estudiante
    When intenta iniciar una sesión en vivo
    Then el sistema responde 403
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — transición de estado simple sobre el aggregate ya construido en `US-6.1.2`, mismo
  patrón de Event Sourcing. Cierra la Iteración 1 sin introducir mecanismos nuevos.

**Capa(s) afectadas:**
- [x] Entities — método `iniciar()` en `ActividadEvaluativaEnVivo`, `SesionEnVivoIniciada`
  (evento), `SesionYaIniciada` (error)
- [x] Use Cases — `IniciarSesionEnVivoUseCase`
- [x] Interface Adapters — método nuevo en `SesionesEnVivoController`
- [x] Frameworks — endpoint `POST /sesiones-en-vivo/{sesion_id}/iniciar`
- [ ] Frontend — diferido, mismo criterio que la Iteración 1 del Incremento 3

---

## Fuente de verdad UX

No aplica a esta US — backend puro. Pantalla correspondiente en
`docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md` §1.2 (Docente, control de sesión),
§2.2/§4.0 (Estudiante/proyección, presentación de pregunta), pendiente de iteración de
frontend.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/actividad_evaluativa/entities/actividad_evaluativa_en_vivo.py` | Método `iniciar()` — valida `estado == EnEspera`, transiciona a `EnCurso` |
| `src/actividad_evaluativa/entities/eventos_en_vivo.py` | `SesionEnVivoIniciada` |
| `src/actividad_evaluativa/entities/errors.py` | `SesionYaIniciada` |
| `src/actividad_evaluativa/use_cases/iniciar_sesion_en_vivo.py` | `IniciarSesionEnVivoUseCase` |
| `src/actividad_evaluativa/interface_adapters/controllers/sesiones_en_vivo_controller.py` | Método `iniciar(...)` |
| `src/actividad_evaluativa/frameworks/api/sesiones_en_vivo_router.py` | `POST /sesiones-en-vivo/{sesion_id}/iniciar` (rol `docente`) |
| `tests/unit/inc6/test_iniciar_sesion_en_vivo.py` | Tests unitarios del Use Case |
| `tests/integration/inc6/test_sesiones_en_vivo_router.py` | Tests HTTP del endpoint (extiende el de `US-6.1.2`/`US-6.1.3`) |
| `tests/features/inc6/US-6.1.4.feature` + step defs | BDD de los criterios de aceptación de arriba |

---

## Referencias

- Modelo de dominio: `docs/design/domain/BC-actividad-evaluativa-modelo.md` §12
  (`IniciarSesionEnVivo` → `SesionEnVivoIniciada`), §16 (mensaje de broadcast, primera fila),
  §17 punto 4 (decisión manual del Docente en cada paso)
- Depende de: `US-6.1.1` (`CanalTiempoRealPort`), `US-6.1.2` (aggregate existente)
- Cierra: Iteración 1 del Incremento 6 (RF-08 + infraestructura WebSockets)
- Candidatas: `docs/plans/inc6/inc6-candidatas.md`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
