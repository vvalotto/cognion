# US-3.2.3: Estudiante finaliza su evaluación y ve la revisión completa

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-3.2`
**Tipo**: `feat backend`
**Agregado principal afectado**: `Evaluacion`
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Estudiante**,
quiero **finalizar explícitamente mi evaluación y ver de inmediato la revisión completa**
para **saber cómo me fue apenas termino — mi respuesta a cada pregunta, si acerté o no, y la
respuesta correcta si fallé (RF-13)**.

---

## Contexto del dominio

### Problema

`US-3.2.1`/`US-3.2.2` dejan a `Evaluacion` en `EnCurso` o `Suspendida`, con `respuestas` ya
persistidas respuesta a respuesta. Falta la transición final del ciclo de vida
(`EnCurso`/`Suspendida → Finalizada`) y la query que RF-13 exige disponible **solo** después de
esa transición — nunca antes, ni siquiera parcialmente durante `EnCurso` (RF-13, criterio de
aceptación exacto: "el detalle completo es visible inmediatamente al finalizar, no antes").
Esta US agrega ambas piezas y cierra el ciclo de vida completo de `Evaluacion` que empezó en
`US-3.1.3`. Habilita a `US-3.2.4` (`VerificadorDeVencimientos`, Regla 2) a disparar
`FinalizarEvaluacion` con actor `Sistema` reutilizando el mismo Use Case tal cual — mismo patrón
que `SuspenderEvaluacion`/`US-3.2.2`.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Aggregate (existente) | `Evaluacion` | Gana la transición `finalizar()` sobre `estado`; gana `respuesta_vigente_de(pregunta_id)` (INV-AE-09, necesario para la revisión) |
| Command | `FinalizarEvaluacion(evaluacion_id)` | `EnCurso`/`Suspendida` → `Finalizada` |
| Domain Event | `EvaluacionFinalizada` | Hecho de dominio — mismo evento sin importar el actor (estudiante o, más adelante, `Sistema` en `US-3.2.4`); el payload distingue `actor`, mismo criterio que `EvaluacionSuspendida` (`US-3.2.2`) |
| Query (sin comando ni evento) | `ObtenerRevisionEvaluacion(evaluacion_id)` | Detalle por pregunta: respuesta propia vigente, correcta/incorrecta, respuesta correcta si falló — solo sobre `Evaluacion` `Finalizada` |

Esta US implementa solo el actor `Estudiante`, explícito vía HTTP, para `FinalizarEvaluacion`.
El campo `actor` del payload de `EvaluacionFinalizada` ya se incluye (valor fijo
`"estudiante"`) para no romper el esquema del evento cuando `US-3.2.4` agregue el disparo
automático con `actor = "sistema"`.

`ObtenerRevisionEvaluacion` es una **query pura**, sin comando ni evento de dominio propio
(`BC-actividad-evaluativa-modelo.md` §4) — no muta `Evaluacion`, solo la lee ya reconstruida y
compone su resultado consultando `PreguntaConsultaPort` por el texto y la respuesta correcta de
cada pregunta asignada.

---

## Especificacion del comportamiento

### Precondicion

- Actor autenticado con JWT válido y claim `rol = estudiante`.
- `US-3.1.3`/`US-3.2.1`/`US-3.2.2` implementadas — existe una `Evaluacion` para
  `evaluacion_id`, perteneciente al estudiante autenticado, con o sin `respuestas` registradas.

### Postcondicion

**`FinalizarEvaluacion`:**
- `Evaluacion.estado` pasa de `EnCurso` o `Suspendida` a `Finalizada`.
- Evento `EvaluacionFinalizada` persistido en el stream de la `Evaluacion`.
- `respuestas` y `preguntas_asignadas` no se modifican.
- A partir de este momento, `RegistrarRespuesta`/`SuspenderEvaluacion`/`ReanudarEvaluacion`
  sobre esta `Evaluacion` rechazan con `EvaluacionYaFinalizada` (ya implementado desde
  `US-3.2.1`/`US-3.2.2` — esta US no cambia esas rutas, solo verifica que sigue vigente).

**`ObtenerRevisionEvaluacion`:**
- Devuelve, por cada `PreguntaAsignada` del set (en su `orden` original): el `pregunta_id`, el
  texto de la pregunta, si el estudiante la respondió, su respuesta vigente (la de
  `confirmada_en` más reciente si hubo reintentos — INV-AE-09) si respondió, si es correcta, y
  la respuesta correcta **solo si falló o no respondió**.
- Incluye un resumen: cantidad de preguntas, cantidad correctas, cantidad incorrectas (una
  pregunta no respondida cuenta como incorrecta a los fines del resumen — ver "Decisiones de
  diseño").

### Invariantes

| ID | Invariante |
|----|------------|
| — (`EvaluacionYaFinalizada`) | `FinalizarEvaluacion` sobre una `Evaluacion` ya `Finalizada` se rechaza — no reemite el evento (idempotencia del comando, no del efecto: a diferencia de `IniciarEvaluacion`, un segundo `FinalizarEvaluacion` es un error, no un no-op silencioso, mismo criterio que `SuspenderEvaluacion`/`ReanudarEvaluacion` en `US-3.2.2`). |
| — (`EvaluacionNoFinalizada`, nuevo error) | `ObtenerRevisionEvaluacion` rechaza si `Evaluacion.estado` es `EnCurso` o `Suspendida` — RF-13 exige que el detalle no exista antes de finalizar. |
| — (`EvaluacionNoExiste`) | Ambos (comando y query) rechazan si `evaluacion_id` no corresponde a ninguna `Evaluacion` existente, o no pertenece al estudiante autenticado. |
| — (`FueraDePeriodo`) | `FinalizarEvaluacion` **no** valida período vigente — a diferencia de `ReanudarEvaluacion`/`RegistrarRespuesta`, finalizar debe poder hacerse en cualquier momento (incluye el caso en que el `VerificadorDeVencimientos`, `US-3.2.4`, lo dispare automáticamente ya pasado `fecha_cierre`, y el caso en que el estudiante decide terminar antes de responder todo el set). |

### Decisiones de diseño (no cubiertas literalmente por RF-13/el modelo)

1. **Pregunta no respondida al finalizar:** el modelo no dice qué pasa si el estudiante
   finaliza sin responder todas las preguntas del set (permitido — no hay invariante que lo
   impida). Esta spec decide: se muestra en la revisión con `respondida = false`, cuenta como
   incorrecta en el resumen, y expone la respuesta correcta (mismo tratamiento que una
   respondida mal, porque el estudiante igual necesita saber cuál era la correcta). A
   confirmar con Víctor si prefiere una tercera categoría "sin responder" separada de
   "incorrecta" — no bloquea esta implementación, documentado para revisión en el reporte de
   cierre.
2. **Reintentos:** si `cantidad_intentos_permitidos` > 1 y el estudiante respondió más de una
   vez la misma pregunta, la revisión usa la respuesta vigente por INV-AE-09 (`confirmada_en`
   más reciente) — mismo criterio que ya aplica `RegistrarRespuesta` para `es_correcta`.

---

## Criterios de aceptacion

```gherkin
Feature: Finalización de la evaluación y revisión completa (US-3.2.3)

  Scenario: Estudiante finaliza una evaluación en curso
    Given una Evaluacion EnCurso con algunas respuestas registradas
    When el Estudiante ejecuta FinalizarEvaluacion(evaluacion_id)
    Then el estado pasa a Finalizada
    And se emite el evento EvaluacionFinalizada

  Scenario: Estudiante finaliza una evaluación suspendida
    Given una Evaluacion Suspendida
    When el Estudiante ejecuta FinalizarEvaluacion(evaluacion_id)
    Then el estado pasa a Finalizada

  Scenario: Rechazo al finalizar una evaluación ya finalizada
    Given una Evaluacion Finalizada
    When el Estudiante intenta FinalizarEvaluacion de nuevo
    Then el sistema rechaza la operación con EvaluacionYaFinalizada

  Scenario: Revisión disponible tras finalizar
    Given una Evaluacion Finalizada con 3 preguntas asignadas, 2 respondidas correctamente y 1 incorrectamente
    When el Estudiante ejecuta ObtenerRevisionEvaluacion(evaluacion_id)
    Then el sistema devuelve el detalle de las 3 preguntas
    And la pregunta incorrecta incluye la respuesta correcta
    And las preguntas correctas no incluyen la respuesta correcta
    And el resumen indica 2 correctas y 1 incorrecta sobre 3

  Scenario: Revisión incluye preguntas no respondidas como incorrectas
    Given una Evaluacion Finalizada con una PreguntaAsignada sin ninguna Respuesta
    When el Estudiante ejecuta ObtenerRevisionEvaluacion(evaluacion_id)
    Then esa pregunta aparece con respondida = false
    And cuenta como incorrecta en el resumen
    And incluye la respuesta correcta

  Scenario: Revisión usa la respuesta vigente ante reintentos
    Given una Evaluacion Finalizada con 2 Respuesta para la misma pregunta, la primera incorrecta y la segunda (más reciente) correcta
    When el Estudiante ejecuta ObtenerRevisionEvaluacion(evaluacion_id)
    Then esa pregunta aparece como correcta con la respuesta más reciente

  Scenario: Rechazo de la revisión antes de finalizar (EnCurso)
    Given una Evaluacion EnCurso
    When el Estudiante intenta ObtenerRevisionEvaluacion
    Then el sistema rechaza la operación con EvaluacionNoFinalizada

  Scenario: Rechazo de la revisión antes de finalizar (Suspendida)
    Given una Evaluacion Suspendida
    When el Estudiante intenta ObtenerRevisionEvaluacion
    Then el sistema rechaza la operación con EvaluacionNoFinalizada
```

---

## Fuera de alcance de esta US

- **Disparo automático por vencimiento del período (Regla 2 del `VerificadorDeVencimientos`)**
  — `US-3.2.4`, reutiliza `FinalizarEvaluacion` tal cual con actor `Sistema`.
- **Cascada síncrona desde `CerrarActividad` (Regla 3)** — `US-3.3.2`, Iteración 3, también
  reutiliza `FinalizarEvaluacion` tal cual.
- **Pantalla de revisión** (`#est-revision`) — `US-3.4.7` (Iteración 4). Esta US solo expone
  los endpoints.

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — usa el event store de `US-3.1.1`, la Unit of Work por Use Case (`ADR-009`) y el
  mismo patrón de replay/append de `US-3.1.3`/`US-3.2.1`/`US-3.2.2`. `EvaluacionesController`
  pasaría de 4 a 5 Use Case inyectados con solo `FinalizarEvaluacionUseCase` (comando, mismo
  agregado) — dentro del patrón ya establecido. `ObtenerRevisionEvaluacionUseCase` es una
  **query** que además depende de `PreguntaConsultaPort` (no solo del event store, a diferencia
  de los demás comandos de `Evaluacion`) — para no repetir el CRITICAL de CBO ya visto tres
  veces en Incremento 2 (`PreguntasController`/`CuentasController`) y evitado a propósito en
  `US-2.1.7`/`US-2.2.2`/`US-2.2.3`/`US-3.2.2`, va en un controller nuevo y separado,
  `RevisionController`, con su propio router — separación command/query, no forzar el diseño
  previo de `EvaluacionesController`.

**Capa(s) afectadas:**
- [x] Entities — método `Evaluacion.finalizar()`/`validar_para_finalizar()`, método
  `respuesta_vigente_de(pregunta_id)` (INV-AE-09), evento `EvaluacionFinalizada`, error
  `EvaluacionNoFinalizada`, actualiza `reconstruir` para reproducir `EvaluacionFinalizada` sobre
  `estado`; nuevo módulo `entities/revision_evaluacion.py` con los Value Objects de resultado
  (`DetallePreguntaRevision`, `RevisionEvaluacion`)
- [x] Entities/Ports — `PreguntaConsultaPort` gana `obtener_detalle_correccion(pregunta_id)`
  (texto + contenido de la respuesta correcta, mismo shape que `contenido` de `Respuesta`) —
  necesario para la revisión, no cubierto por `evaluar_correccion` (que solo devuelve `bool`)
- [x] Use Cases — `FinalizarEvaluacionUseCase` (carga `Evaluacion` por replay, valida, arma el
  evento, invoca `EventStorePort.append` con concurrencia optimista, mismo patrón que
  `SuspenderEvaluacionUseCase`); `ObtenerRevisionEvaluacionUseCase` (carga `Evaluacion`, valida
  `Finalizada`, arma el detalle consultando `PreguntaConsultaPort` por cada `PreguntaAsignada`)
- [x] Interface Adapters — extiende `EvaluacionesController` con `finalizar_evaluacion`;
  controller nuevo `RevisionController` con `obtener_revision`
- [x] Frameworks — endpoint FastAPI `POST /evaluaciones/{evaluacion_id}/finalizar` (rol
  `estudiante`) en `evaluaciones_router.py`; endpoint nuevo `GET /evaluaciones/{evaluacion_id}/revision`
  (rol `estudiante`) en `revision_router.py`; implementa `obtener_detalle_correccion` en
  `PreguntaConsultaPortInProcess`; registra `RevisionController`/`FinalizarEvaluacionUseCase` en
  `dependencies.py`; registra `revision_router` en `src/app.py`
- [ ] Frontend — cubierto por `US-3.4.7` (Iteración 4)

---

## Fuente de verdad UX

No aplica a esta spec (backend puro) — la pantalla de revisión (`#est-revision`) se especifica
en `US-3.4.7`, wireframe ya aprobado en `docs/design/ux/wireframes-actividad-evaluativa.md` §3.5
(resumen correctas/incorrectas/total, detalle por pregunta con enunciado, badge, respuesta
propia y — solo si falló — la correcta).

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/actividad_evaluativa/entities/evaluacion.py` | `finalizar()`/`validar_para_finalizar()`, `respuesta_vigente_de(pregunta_id)`, actualiza `reconstruir`/`_aplicar_evento` para `EvaluacionFinalizada` |
| `src/actividad_evaluativa/entities/eventos.py` | `EvaluacionFinalizada` (agrega al archivo existente) |
| `src/actividad_evaluativa/entities/errors.py` | `EvaluacionNoFinalizada` |
| `src/actividad_evaluativa/entities/revision_evaluacion.py` | Nuevo — `DetallePreguntaRevision`, `RevisionEvaluacion` (Value Objects de resultado de la query) |
| `src/actividad_evaluativa/entities/ports/pregunta_consulta_port.py` | Nuevo método `obtener_detalle_correccion(pregunta_id)` + VO `DetalleCorreccionPregunta` |
| `src/actividad_evaluativa/frameworks/adapters/pregunta_consulta_port_in_process.py` | Implementa `obtener_detalle_correccion` |
| `src/actividad_evaluativa/use_cases/finalizar_evaluacion.py` | Nuevo — orquesta la transición, invoca `EventStorePort.append` |
| `src/actividad_evaluativa/use_cases/obtener_revision_evaluacion.py` | Nuevo — query, arma `RevisionEvaluacion` |
| `src/actividad_evaluativa/interface_adapters/controllers/evaluaciones_controller.py` | Método nuevo `finalizar_evaluacion`, un Use Case más inyectado |
| `src/actividad_evaluativa/interface_adapters/controllers/revision_controller.py` | Nuevo — `RevisionController` con `obtener_revision` |
| `src/actividad_evaluativa/frameworks/api/evaluaciones_router.py` | Endpoint `POST /evaluaciones/{evaluacion_id}/finalizar` |
| `src/actividad_evaluativa/frameworks/api/revision_router.py` | Nuevo — endpoint `GET /evaluaciones/{evaluacion_id}/revision` |
| `src/actividad_evaluativa/frameworks/api/schemas.py` | `RevisionEvaluacionResponse`, `DetallePreguntaRevisionResponse` |
| `src/actividad_evaluativa/frameworks/dependencies.py` | Registra `FinalizarEvaluacionUseCase` en `get_evaluaciones_controller`; nuevo `get_revision_controller` |
| `src/app.py` | `app.include_router(revision_router)` |

---

## Referencias

- Depende de: `US-3.1.1` (event store), `US-3.1.3` (`Evaluacion` existente), `US-3.2.1`
  (`respuestas` ya persistidas), `US-3.2.2` (`EvaluacionYaFinalizada` ya usado como error de
  `SuspenderEvaluacion`/`ReanudarEvaluacion`)
- Relacionada con: `US-3.2.4` (`VerificadorDeVencimientos` reutiliza `FinalizarEvaluacion` con
  actor `Sistema`, Regla 2), `US-3.3.2` (`CerrarActividad` reutiliza `FinalizarEvaluacion` en
  cascada síncrona, Regla 3), `US-3.4.7` (pantalla de revisión, Iteración 4)
- Modelo de dominio: `docs/design/domain/BC-actividad-evaluativa-modelo.md` §3 (comandos),
  §4 (tabla comando→evento, incluye la query `ObtenerRevisionEvaluacion`), §5 (`Evaluacion`),
  §7 (`PreguntaConsultaPort`)
- Candidatas: `docs/plans/inc3/inc3-candidatas.md`
- Issue: [#158](https://github.com/vvalotto/cognion/issues/158)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
