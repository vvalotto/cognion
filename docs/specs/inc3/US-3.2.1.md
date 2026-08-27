# US-3.2.1: Estudiante confirma una respuesta (persistencia atómica)

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-3.2`
**Tipo**: `feat backend`
**Agregado principal afectado**: `Evaluacion`
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Estudiante**,
quiero **confirmar mi respuesta a una pregunta de mi evaluación y que quede guardada al
instante**
para **no perder esa respuesta si me desconecto justo después de confirmarla (RNF
Confiabilidad, RF-13)**.

---

## Contexto del dominio

### Problema

Abre la Iteración 2: sin `RegistrarRespuesta` el set de preguntas fijado en `US-3.1.3` no tiene
ninguna respuesta que registrar, y no hay nada que `US-3.2.2` (suspender/reanudar) ni `US-3.2.3`
(finalizar + revisión) puedan operar. Es la primera vez que el BC persiste dentro de una
transacción por confirmación individual (`ADR-009`) en vez de una sola vez al final de un
comando — la garantía central de la que depende el DoD del incremento (desconexión simulada,
cero pérdida de respuestas).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Entity (nueva, dentro de `Evaluacion.respuestas`) | `Respuesta` | `id` propio, `pregunta_id`, `numero_intento`, `contenido`, `es_correcta`, `confirmada_en` — inmutable una vez creada (INV-AE-09) |
| Command | `RegistrarRespuesta(evaluacion_id, pregunta_id, contenido)` | Crea una `Respuesta` nueva y la agrega a `Evaluacion.respuestas` |
| Domain Event | `RespuestaRegistrada` | Única fuente de verdad de la respuesta — persistida en su propia transacción (INV-AE-09) |
| Port (ampliado) | `PreguntaConsultaPort` → BC Banco de Preguntas | Nuevo método `evaluar_correccion(pregunta_id, contenido)` — calcula `es_correcta` consultando el estado vigente de la `PreguntaPlantilla` (INV-AE-10), sin exponer el aggregate de Banco de Preguntas fuera de su BC |

`contenido` no tiene una forma única — depende del tipo concreto de `PreguntaPlantilla`
(`US-2.1.3`/`US-2.1.4`), resuelto del lado de Banco de Preguntas, nunca por Actividad
Evaluativa:

| Tipo de pregunta | Forma de `contenido` |
|---|---|
| `PreguntaPlantillaOpcionMultiple` | `{"opcion_indice": int}` — posición dentro de `opciones` (la `Opcion` no tiene `id` propio, `banco_preguntas/entities/opcion.py`) |
| `PreguntaPlantillaVerdaderoFalso` | `{"valor": bool}` |

---

## Especificacion del comportamiento

### Precondicion

- Actor autenticado con JWT válido y claim `rol = estudiante`.
- `US-3.1.3` implementada — existe una `Evaluacion` para `(actividad_id, estudiante_id)` del
  estudiante autenticado, identificada por `evaluacion_id`.
- `pregunta_id` corresponde a una `PreguntaPlantilla` existente en BC Banco de Preguntas.

### Postcondicion

- Nueva `Respuesta` (Entity, `id` propio) creada y agregada a `Evaluacion.respuestas`, con
  `es_correcta` ya calculado (INV-AE-10) y `numero_intento` incrementado respecto de la última
  `Respuesta` existente para el mismo `pregunta_id` (o `1` si es la primera).
- Evento `RespuestaRegistrada` persistido en su propia transacción (Unit of Work por Use Case,
  `ADR-009`) — commit atómico apenas se confirma, sin esperar a `FinalizarEvaluacion`.
- Ninguna `Respuesta` existente se modifica ni se borra (INV-AE-09) — la más reciente
  (`confirmada_en` mayor) por `pregunta_id` es la vigente para puntaje y revisión (`US-3.2.3`).
- El estudiante **no** recibe en la respuesta HTTP si acertó o no (hot spot resuelto en el
  modelo de dominio, §5 de `BC-actividad-evaluativa-modelo.md`) — solo la confirmación de que
  quedó registrada.

### Invariantes

| ID | Invariante |
|----|------------|
| INV-AE-07 | `pregunta_id` debe pertenecer al set `preguntas_asignadas` de la `Evaluacion` — `PreguntaNoAsignada` si no. La actividad debe estar dentro de su período vigente (`fecha_apertura` ≤ ahora ≤ `fecha_cierre` vigente, incluida cualquier extensión futura de `US-3.3.1`) — `FueraDePeriodo` si no (reutiliza el error de `US-3.1.3`). |
| INV-AE-08 | La cantidad de `Respuesta` ya registradas para ese `pregunta_id` no puede superar `cantidad_intentos_permitidos` de la actividad — `IntentosAgotados` si se excede. |
| INV-AE-09 | Cada `Respuesta` se crea y persiste en su propia transacción al momento de la confirmación — cero pérdida ante desconexión inmediatamente después. Entidad inmutable: nunca se modifica ni se borra una `Respuesta` existente. |
| INV-AE-10 | `es_correcta` se calcula en el momento de crear la `Respuesta`, comparando contra el estado vigente de la `PreguntaPlantilla` en ese instante — inmutable a ediciones posteriores de esa pregunta en el banco. |
| INV-AE-12 | `RegistrarRespuesta` requiere `Evaluacion.estado = EnCurso` — `EvaluacionSuspendida` si está `Suspendida` (el estudiante debe `ReanudarEvaluacion` primero, `US-3.2.2`), `EvaluacionYaFinalizada` si está `Finalizada`. |
| — (`EvaluacionNoExiste`) | Rechaza si `evaluacion_id` no corresponde a ninguna `Evaluacion` existente, o no pertenece al estudiante autenticado. |

---

## Criterios de aceptacion

```gherkin
Feature: Registro de respuesta con persistencia atómica (US-3.2.1)

  Scenario: Estudiante confirma una respuesta válida (opción múltiple)
    Given una Evaluacion EnCurso con una PreguntaAsignada de tipo opción múltiple
    When el Estudiante ejecuta RegistrarRespuesta(evaluacion_id, pregunta_id, {opcion_indice: 1})
    Then el sistema crea una Respuesta con numero_intento=1 y es_correcta calculado
    And se emite el evento RespuestaRegistrada
    And la respuesta HTTP no informa si es_correcta

  Scenario: Segundo intento sobre la misma pregunta (dentro del límite)
    Given una Evaluacion EnCurso con cantidad_intentos_permitidos=2
    And ya existe una Respuesta previa (numero_intento=1) para esa pregunta
    When el Estudiante confirma una nueva respuesta para la misma pregunta
    Then el sistema crea una segunda Respuesta con numero_intento=2
    And ambas Respuesta conviven en la colección — la de numero_intento=2 es la vigente

  Scenario: Rechazo por intentos agotados
    Given una Evaluacion EnCurso con cantidad_intentos_permitidos=1
    And ya existe una Respuesta previa para esa pregunta
    When el Estudiante intenta confirmar una nueva respuesta para la misma pregunta
    Then el sistema rechaza la operación con IntentosAgotados
    And no se persiste ninguna Respuesta nueva

  Scenario: Rechazo por pregunta no asignada
    Given una Evaluacion EnCurso
    When el Estudiante ejecuta RegistrarRespuesta con un pregunta_id fuera de su set asignado
    Then el sistema rechaza la operación con PreguntaNoAsignada

  Scenario: Rechazo sobre evaluación suspendida
    Given una Evaluacion en estado Suspendida
    When el Estudiante intenta RegistrarRespuesta
    Then el sistema rechaza la operación con EvaluacionSuspendida

  Scenario: Rechazo sobre evaluación finalizada
    Given una Evaluacion en estado Finalizada
    When el Estudiante intenta RegistrarRespuesta
    Then el sistema rechaza la operación con EvaluacionYaFinalizada

  Scenario: Rechazo fuera del período vigente
    Given una Evaluacion EnCurso cuya actividad ya pasó su fecha_cierre
    When el Estudiante intenta RegistrarRespuesta
    Then el sistema rechaza la operación con FueraDePeriodo

  Scenario: Persistencia atómica ante desconexión simulada
    Given un Estudiante que confirma una Respuesta
    When el proceso backend se reinicia inmediatamente después de la confirmación
    Then la Respuesta persiste en el event store al reiniciar el proceso
    And se reconstruye correctamente por replay del stream de la Evaluacion
```

---

## Fuera de alcance de esta US

- **Feedback inmediato de corrección al estudiante** — decisión de dominio ya fijada
  (`BC-actividad-evaluativa-modelo.md` §5, "Sin feedback inmediato"): el detalle completo recién
  es visible al `FinalizarEvaluacion` (`US-3.2.3`, RF-13).
- **Suspender/reanudar la evaluación** — `US-3.2.2`.
- **Mostrar el enunciado y capturar la elección en pantalla** — `US-3.4.6` (Iteración 4). Esta
  US solo expone el endpoint que registra la confirmación ya resuelta por el cliente.

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — usa el event store de `US-3.1.1`, la Unit of Work por Use Case ya ratificada
  (`ADR-009`) y el patrón de puerto entre BCs ya usado por `PreguntaConsultaPort` desde
  `US-3.1.2`/`US-3.1.3`. Ampliar ese puerto con `evaluar_correccion` sigue el mismo criterio de
  "no ensanchar innecesariamente, agregar el método que hace falta" de `US-2.1.9`.

**Capa(s) afectadas:**
- [x] Entities — `Respuesta` (Entity nueva), método `Evaluacion.registrar_respuesta(...)`
  (aplica INV-AE-07/08/12 sobre el estado ya cargado), evento `RespuestaRegistrada`, errores
  `PreguntaNoAsignada`/`IntentosAgotados`/`EvaluacionSuspendida`/`EvaluacionYaFinalizada`/
  `EvaluacionNoExiste`, método nuevo `PreguntaConsultaPort.evaluar_correccion`
- [x] Use Cases — `RegistrarRespuestaUseCase` (carga `ActividadEvaluativaPeriodoAbierto` y
  `Evaluacion` por replay, valida invariantes, calcula `es_correcta` vía el puerto, arma el
  evento, invoca `EventStorePort.append` con concurrencia optimista)
- [x] Interface Adapters — extiende `EvaluacionesController` con `registrar_respuesta`
  (segundo Use Case inyectado, todavía lejos del umbral de CBO que disparó el patrón de
  Incremento 2)
- [x] Frameworks — endpoint FastAPI `POST /evaluaciones/{evaluacion_id}/respuestas` (requiere
  rol `estudiante`); `PreguntaConsultaPortInProcess.evaluar_correccion` reutiliza
  `PreguntaRepositoryPort.obtener_por_id` para comparar `contenido` contra el aggregate vigente
  (`Opcion.es_correcta` por índice, o `respuesta_correcta` para Verdadero/Falso)
- [ ] Frontend — cubierto por `US-3.4.6` (Iteración 4)

---

## Fuente de verdad UX

No aplica a esta spec (backend puro) — la pantalla de rendir (`#est-rendir`) se especifica en
`US-3.4.6`, wireframe ya aprobado en `docs/design/ux/wireframes-actividad-evaluativa.md` §3.3.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/actividad_evaluativa/entities/evaluacion.py` | Entity `Respuesta`, campo `respuestas` en `Evaluacion`, método `registrar_respuesta(...)` (INV-AE-07/08/12), actualiza `reconstruir` para reproducir también `RespuestaRegistrada` |
| `src/actividad_evaluativa/entities/eventos.py` | `RespuestaRegistrada` (agrega al archivo existente) |
| `src/actividad_evaluativa/entities/errors.py` | `PreguntaNoAsignada`, `IntentosAgotados`, `EvaluacionSuspendida`, `EvaluacionYaFinalizada`, `EvaluacionNoExiste` |
| `src/actividad_evaluativa/entities/ports/pregunta_consulta_port.py` | Método nuevo `evaluar_correccion(pregunta_id, contenido) -> bool` |
| `src/actividad_evaluativa/use_cases/registrar_respuesta.py` | Orquesta INV-AE-07/08/09/10/12, calcula corrección vía el puerto, invoca `EventStorePort.append` |
| `src/actividad_evaluativa/interface_adapters/controllers/evaluaciones_controller.py` | Método nuevo `registrar_respuesta`, segundo Use Case inyectado |
| `src/actividad_evaluativa/frameworks/adapters/pregunta_consulta_port_in_process.py` | Implementación de `evaluar_correccion` — reutiliza `PreguntaRepositoryPort.obtener_por_id`, distingue por tipo concreto de `PreguntaPlantilla` |
| `src/actividad_evaluativa/frameworks/api/evaluaciones_router.py` | Endpoint `POST /evaluaciones/{evaluacion_id}/respuestas` |
| `src/actividad_evaluativa/frameworks/api/schemas.py` | `RegistrarRespuestaRequest`/`RespuestaResponse` |
| `src/actividad_evaluativa/frameworks/dependencies.py` | Registra el Use Case ampliado |

---

## Referencias

- Depende de: `US-3.1.1` (event store), `US-3.1.2` (actividad y su período vigente),
  `US-3.1.3` (set de preguntas asignado sobre el que se responde)
- Relacionada con: `US-3.2.2` (`ReanudarEvaluacion` habilita volver a `RegistrarRespuesta` tras
  una suspensión), `US-3.2.3` (consume `respuestas` para el puntaje y la revisión, RF-13),
  `US-3.2.4` (`VerificadorDeVencimientos` usa `ultima_actividad_en`, actualizado por cada
  `RespuestaRegistrada`)
- Modelo de dominio: `docs/design/domain/BC-actividad-evaluativa-modelo.md` §3 (comando),
  §5 (`Evaluacion`, `Respuesta`, INV-AE-07 a INV-AE-12), §6 (persistencia atómica, concurrencia
  optimista), §7 (`PreguntaConsultaPort`, corrección vigente)
- Candidatas: `docs/plans/inc3/inc3-candidatas.md`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
