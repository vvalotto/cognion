# US-6.1.3: Estudiante se une a una sesión en vivo

**Estado**: `Implementada`
**Iteracion / Sprint**: `INC-6.1`
**Tipo**: `feature backend`
**Agregado principal afectado**: `ParticipacionEnVivo`
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Estudiante**,
quiero **unirme a una sesión en vivo desde mi portal, ya sea mientras espera que arranque o
incluso después de que ya empezó**,
para **participar de la dinámica en el momento, sin quedar afuera si llegué un poco tarde**.

---

## Contexto del dominio

### Problema

Segundo aggregate del modo en vivo (`ParticipacionEnVivo`, mismo criterio de "un aggregate por
`(sesion_id, estudiante_id)`" que `Evaluacion` en período abierto, §2/§11) — evita que
`ActividadEvaluativaEnVivo` crezca con el estado de cada estudiante. Esta US solo cubre la
unión (`EstudianteUnido`); las respuestas (`RespuestaEnVivoRegistrada`) son la Iteración 2.

Union tardía **confirmada y permitida** (hot spot 2, §17): un estudiante puede unirse en
cualquier momento mientras la sesión no esté `Finalizada`, incluso ya `EnCurso` — participa
recién desde la pregunta en la que se unió.

Esta es la primera US que **publica** por el canal de tiempo real (`US-6.1.1`): el Docente, en
la sala de espera, ve la lista de participantes actualizarse en vivo a medida que se unen.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Aggregate (nuevo) | `ParticipacionEnVivo` | Root — `id`, `sesion_id`, `estudiante_id`, `unido_en`, `respuestas` (vacía en esta US) (`BC-actividad-evaluativa-modelo.md` §14) |
| Comando | `UnirseASesionEnVivo(sesion_id, estudiante_id)` | Idempotente — no-op si ya existe la `ParticipacionEnVivo` |
| Evento | `EstudianteUnido` | Payload: `sesion_id`, `estudiante_id`, `unido_en` |
| Read model (nuevo) | `participantes_por_sesion` `(sesion_id, estudiante_id, unido_en)` | Actualizado síncronamente en la misma transacción del evento (§15) — sostiene la sala de espera del Docente |
| Use Case (nuevo) | `UnirseASesionEnVivoUseCase` | Valida que la sesión exista y no esté `Finalizada`, hace `append`/no-op sobre el stream de `ParticipacionEnVivo`, actualiza `participantes_por_sesion`, publica por `CanalTiempoRealPort` (`US-6.1.1`) |
| Endpoint (nuevo) | `POST /sesiones-en-vivo/{sesion_id}/unirse` | Rol `estudiante` |

---

## Especificacion del comportamiento

### Precondicion

- `US-6.1.1` y `US-6.1.2` cerradas — existe al menos una `ActividadEvaluativaEnVivo`.
- Estudiante autenticado, existente (`EstudianteConsultaPort`, ya existente).

### Postcondicion

- Si no existía `ParticipacionEnVivo` para `(sesion_id, estudiante_id)`: se crea, se persiste
  `EstudianteUnido` como primer evento de su stream, y se agrega la fila correspondiente a
  `participantes_por_sesion`.
- Si ya existía: no se persiste ningún evento nuevo ni se actualiza el read model — respuesta
  idempotente (mismo `estudiante_id`, mismo resultado), sin error.
- En ambos casos se publica por `CanalTiempoRealPort.publicar(sesion_id, ...)` el conteo/lista
  de participantes actualizada — dirigido al Docente en su vista de sala de espera
  (`BC-actividad-evaluativa-modelo.md` §16, última fila). Publicar en el caso idempotente
  también es correcto (el conteo no cambia, pero no es un error retransmitirlo) — más simple
  que distinguir el caso "ya unido" solo para omitir el broadcast.
- Respuesta HTTP `200` (no `201`, dado el criterio idempotente) con la confirmación de unión.

### Invariantes

| ID | Invariante |
|----|------------|
| INV-AEV-06 | A lo sumo una `ParticipacionEnVivo` por `(sesion_id, estudiante_id)` — `UnirseASesionEnVivo` es idempotente si ya existe. |

### Excepciones

| Excepción | Condición |
|---|---|
| `SesionNoExiste` | `sesion_id` no corresponde a ninguna `ActividadEvaluativaEnVivo` (404) |
| `SesionYaFinalizada` | La sesión ya está en estado `Finalizada` — no se puede unir después del cierre (422) |

---

## Criterios de aceptacion

```gherkin
Feature: Estudiante se une a una sesión en vivo (US-6.1.3)

  Scenario: Unión mientras la sesión está en espera
    Given una sesión en vivo en estado EnEspera
    When el Estudiante se une
    Then se crea su ParticipacionEnVivo y aparece en participantes_por_sesion
    And el Docente conectado al canal recibe la lista de participantes actualizada

  Scenario: Unión tardía, sesión ya en curso
    Given una sesión en vivo en estado EnCurso, en la tercera pregunta
    When un Estudiante que no se había unido antes se une ahora
    Then su ParticipacionEnVivo se crea igualmente, sin respuestas previas registradas

  Scenario: Unión idempotente
    Given un Estudiante ya unido a una sesión
    When intenta unirse de nuevo (ej. reconexión de red)
    Then el sistema responde 200 sin crear una segunda ParticipacionEnVivo

  Scenario: Rechazo por sesión finalizada
    Given una sesión en vivo en estado Finalizada
    When un Estudiante intenta unirse
    Then el sistema rechaza la operación con SesionYaFinalizada (422)

  Scenario: Sesión inexistente
    Given un sesion_id que no corresponde a ninguna sesión en vivo
    When un Estudiante intenta unirse
    Then el sistema rechaza la operación con SesionNoExiste (404)
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — segundo aggregate del BC siguiendo el mismo patrón CQRS/Event Sourcing ya validado
  (`Evaluacion`/`ActividadEvaluativaPeriodoAbierto`, §2), con la única pieza nueva siendo la
  publicación por `CanalTiempoRealPort` (ya resuelta en `US-6.1.1`).

**Capa(s) afectadas:**
- [x] Entities — `ParticipacionEnVivo` (aggregate), `EstudianteUnido` (evento),
  `SesionYaFinalizada` (error)
- [x] Use Cases — `UnirseASesionEnVivoUseCase`
- [x] Interface Adapters — método nuevo en `SesionesEnVivoController` (o controller propio si
  el CBO del controller existente se acerca al umbral — a evaluar en Fase 2 de
  `/implement-us`, mismo criterio ya aplicado repetidamente en el proyecto,
  `feedback_cbo_pre_push_no_fase7`)
- [x] Frameworks — endpoint `POST /sesiones-en-vivo/{sesion_id}/unirse`, adapter del read model
  `participantes_por_sesion` (tabla nueva o proyección sobre `events`, a decidir en Fase 2 —
  mismo criterio que `US-3.2.4` evaluó para `EvaluacionActivaQueryPort`: tabla propia vs. query
  de lectura sobre `events`)
- [ ] Frontend — diferido, mismo criterio que la Iteración 1 del Incremento 3

---

## Fuente de verdad UX

No aplica a esta US — backend puro. Pantalla correspondiente (sala de espera del Docente,
pantalla de espera del Estudiante) en
`docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md` §1.1/§2.1, pendiente de iteración
de frontend.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/actividad_evaluativa/entities/participacion_en_vivo.py` | Aggregate `ParticipacionEnVivo` — constructor/factory `unirse(...)` |
| `src/actividad_evaluativa/entities/eventos_en_vivo.py` | `EstudianteUnido` |
| `src/actividad_evaluativa/entities/errors.py` | `SesionYaFinalizada` (si no existe ya con ese nombre para este agregado) |
| `src/actividad_evaluativa/entities/ports/participantes_sesion_query_port.py` | Puerto de lectura de `participantes_por_sesion` (o reuso de un query port ya existente, a decidir en Fase 2) |
| `src/actividad_evaluativa/use_cases/unirse_a_sesion_en_vivo.py` | `UnirseASesionEnVivoUseCase` |
| `src/actividad_evaluativa/interface_adapters/controllers/sesiones_en_vivo_controller.py` | Método `unirse(...)` |
| `src/actividad_evaluativa/frameworks/api/sesiones_en_vivo_router.py` | `POST /sesiones-en-vivo/{sesion_id}/unirse` (rol `estudiante`) |
| `src/actividad_evaluativa/frameworks/adapters/participantes_sesion_query_repository.py` | Implementación del read model |
| `tests/unit/inc6/test_unirse_a_sesion_en_vivo.py` | Tests unitarios del Use Case |
| `tests/integration/inc6/test_sesiones_en_vivo_router.py` | Tests HTTP del endpoint (extiende el de `US-6.1.2`) |
| `tests/features/inc6/US-6.1.3.feature` + step defs | BDD de los criterios de aceptación de arriba |

---

## Referencias

- Modelo de dominio: `docs/design/domain/BC-actividad-evaluativa-modelo.md` §12, §13
  (`UnirseASesionEnVivo` → `EstudianteUnido`), §14 (`ParticipacionEnVivo`, INV-AEV-06), §15
  (`participantes_por_sesion`), §17 punto 2 (unión tardía confirmada)
- Depende de: `US-6.1.1` (`CanalTiempoRealPort`), `US-6.1.2` (existencia de la sesión)
- Consumida por: `US-6.1.4` y toda la Iteración 2
- Candidatas: `docs/plans/inc6/inc6-candidatas.md`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
