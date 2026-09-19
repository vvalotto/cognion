# US-6.2.8: Consultar el estado de la sesión, sus participantes y su ranking

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-6.2`
**Tipo**: `feature backend` (consultas — sin comando ni evento de dominio)
**Agregado principal afectado**: — (lecturas sobre `ActividadEvaluativaEnVivo` y los read models de `US-6.2.3`)
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Docente o Estudiante**,
quiero **volver a ver el estado de la sesión si se me cae la conexión o entro tarde**,
para **retomar exactamente donde estaba la clase, sin perder mi lugar**.

---

## Contexto del dominio

### Problema

Todo el estado en vivo viaja por **WebSocket como broadcast**: un cliente que se conecta (o se
reconecta) **después** de un mensaje no lo recibe. El modelo dejó "manejo de reconexión de un
cliente ya unido" como pendiente de definir (`BC-actividad-evaluativa-modelo.md` §17, "Pendiente
de definir en la spec de implementación"): la reconexión **no debe perder la `ParticipacionEnVivo`,
solo re-suscribirse al canal**. Para que pueda ponerse al día necesita **consultar** el estado por
HTTP.

Esta US agrega tres lecturas thin, sin lógica de negocio nueva. También cubre el otro hueco: el
Estudiante solo ve el ranking al finalizar (§17 punto 10) y la sala de espera del Docente solo se
actualiza por broadcast (`US-6.1.3`).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Query | `ObtenerEstadoDeSesion(sesion_id, solicitante)` | Estado actual reconstruido del stream + contenido de la pregunta actual |
| Query | `ListarParticipantesDeSesion(sesion_id)` | Ya existe como port (`ParticipantesSesionQueryPort`, `US-6.1.3`); se expone por HTTP |
| Query | `ObtenerRankingDeSesion(sesion_id)` | Lee `ranking_por_sesion` (`US-6.2.3`) |
| Use Cases (nuevos) | `ObtenerEstadoSesionUseCase`, `ListarParticipantesUseCase`, `ObtenerRankingUseCase` | Lecturas |
| Controller (nuevo) | `SesionesEnVivoQueryController` | Separado del controller de comandos (command/query, evita CBO) |
| Endpoints (nuevos) | `GET /sesiones-en-vivo/{sesion_id}`, `GET .../participantes`, `GET .../ranking` | Ver roles abajo |

### Contenido de `GET /sesiones-en-vivo/{sesion_id}`

`estado`, `comision_id`, `cantidad_preguntas`, `tiempo_limite_por_pregunta_segundos`,
`pregunta_actual_indice`, `opciones_mostradas`, `opciones_mostradas_en`, `pregunta_actual_cerrada`, y
`pregunta_actual` cuando hay una: `{pregunta_id, enunciado, tipo}` siempre; `opciones` **solo si**
`opciones_mostradas`; `respuesta_correcta` **solo si** `pregunta_actual_cerrada`.

Con `opciones_mostradas_en` y `tiempo_limite_por_pregunta_segundos` el cliente calcula el tiempo
que le queda sin que el servidor mande ticks. Para el **Estudiante** se suman `ya_respondio`
(sobre la pregunta actual) y `puntaje_acumulado` propio (sale de su `ParticipacionEnVivo`).

**Nunca** se expone la respuesta correcta antes de cerrar la pregunta.

### Roles y reglas

| Endpoint | Rol | Regla |
|---|---|---|
| `GET /sesiones-en-vivo/{sesion_id}` | `docente`, `estudiante` | Estudiante recibe además `ya_respondio` y `puntaje_acumulado` |
| `GET .../participantes` | `docente` | Sala de espera (lista de `estudiante_id`, `unido_en`) |
| `GET .../ranking` | `docente`, `estudiante` | Docente: en cualquier momento. **Estudiante: solo con la sesión `Finalizada`** (§17 punto 10); antes → `403` |

---

## Especificacion del comportamiento

### Precondicion

- `US-6.2.3` cerrada (read models) y `US-6.2.7` (para que exista `Finalizada` por API).

### Postcondicion

- Ninguna escritura: no hay evento ni cambio de estado.
- Un cliente reconectado reconstruye su pantalla con una sola llamada al estado.

### Excepciones

| Excepción | Condición | HTTP |
|---|---|---|
| `SesionNoExiste` | sin stream | 404 |
| `RankingNoDisponible` (nueva) | Estudiante pide el ranking con la sesión no `Finalizada` | 403 |
| — | rol no permitido para el endpoint | 403 |

---

## Criterios de aceptacion

```gherkin
Feature: Consultar el estado de la sesión en vivo (US-6.2.8)

  Scenario: Estado de una sesión en espera
    Given una sesión EnEspera
    When un Docente consulta el estado
    Then recibe estado EnEspera sin pregunta actual

  Scenario: Estado con el enunciado presentado y las opciones ocultas
    Given una sesión EnCurso con solo el enunciado presentado
    When un Estudiante consulta el estado
    Then recibe el enunciado sin opciones y sin respuesta correcta

  Scenario: Estado con las opciones mostradas
    Given una pregunta con las opciones mostradas
    When un Estudiante consulta el estado
    Then recibe las opciones, el instante en que se mostraron y el tiempo límite
    And no recibe la respuesta correcta

  Scenario: Estado con la pregunta cerrada
    Given una pregunta cerrada
    When un Estudiante consulta el estado
    Then recibe también la respuesta correcta

  Scenario: El Estudiante ve su propio avance
    Given un Estudiante que ya respondió la pregunta actual con 1200 puntos acumulados
    When consulta el estado
    Then ya_respondio es verdadero y puntaje_acumulado es 1200

  Scenario: Listado de participantes para la sala de espera
    Given tres Estudiantes unidos
    When el Docente lista los participantes
    Then recibe los tres en orden de unión

  Scenario: El Docente ve el ranking en cualquier momento
    Given una sesión EnCurso con puntajes acumulados
    When el Docente consulta el ranking
    Then recibe el ranking ordenado con posición

  Scenario: El Estudiante ve el ranking solo al finalizar
    Given una sesión EnCurso
    When un Estudiante consulta el ranking
    Then el sistema responde 403
    But con la sesión Finalizada recibe el ranking completo

  Scenario: Sesión inexistente
    Given un sesion_id que no corresponde a ninguna sesión
    When se consulta el estado
    Then el sistema responde 404

  Scenario: Rechazo por rol en los participantes
    Given un usuario autenticado con rol Estudiante
    When intenta listar los participantes
    Then el sistema responde 403
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — lecturas sobre lo ya construido; controller de consultas separado del de comandos
  (mismo criterio que `ActividadesQueryController`).

**Capa(s) afectadas:**
- [x] Entities — `RankingNoDisponible`
- [x] Use Cases — tres use cases de lectura
- [x] Interface Adapters — `SesionesEnVivoQueryController`
- [x] Frameworks — tres endpoints, schemas, wiring
- [ ] Frontend — diferido

---

## Fuente de verdad UX

No aplica — backend puro. Pantallas de reconexión, sala de espera y resultado final en
`docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md`, pendientes de frontend.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/actividad_evaluativa/entities/errors.py` | `RankingNoDisponible` |
| `src/actividad_evaluativa/use_cases/obtener_estado_sesion.py`, `listar_participantes.py`, `obtener_ranking.py` | Casos de uso de lectura (nuevos) |
| `src/actividad_evaluativa/interface_adapters/controllers/sesiones_en_vivo_query_controller.py` | Controller de consultas (nuevo) |
| `src/actividad_evaluativa/frameworks/api/sesiones_en_vivo_router.py`, `schemas.py`, `dependencies.py` | Endpoints, schemas, wiring |
| `tests/unit/inc6/`, `tests/integration/inc6/`, `tests/features/inc6/US-6.2.8*.feature` + step defs | Unitarios, HTTP, BDD |

---

## Referencias

- Modelo: `docs/design/domain/BC-actividad-evaluativa-modelo.md` §13 (queries), §14, §15, §16, §17 punto 10 y "Pendiente de definir"
- Precedente de controller de consultas: `ActividadesQueryController` (`US-3.4.2`)
- Depende de: `US-6.2.3`, `US-6.2.7` (y `US-6.2.2`/`US-6.2.5` para los campos de estado)
- Candidatas: `docs/plans/inc6/inc6-candidatas.md`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
