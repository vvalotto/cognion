# US-3.1.3: Estudiante inicia su evaluación (set aleatorio fijo)

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-3.1`
**Tipo**: `feat backend`
**Agregado principal afectado**: `Evaluacion`
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Estudiante**,
quiero **iniciar mi evaluación dentro de una actividad de período abierto y recibir un set de
preguntas propio**
para **empezar a responder sabiendo que ese set no cambia si me reconecto (RF-12, RNF
Confiabilidad)**.

---

## Contexto del dominio

### Problema

Cierra la Iteración 1: sin `IniciarEvaluacion`, la actividad creada en `US-3.1.2` no tiene
ningún estudiante rindiendo. El set de preguntas se sampletea al azar por estudiante (RF-12) y
queda fijo desde este momento — es la garantía de la que depende toda la Iteración 2
(`RegistrarRespuesta`, `US-3.2.1`, solo acepta respuestas sobre preguntas de este set).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Aggregate (nuevo, un stream por `(actividad_id, estudiante_id)`) | `Evaluacion` | `id`, `actividad_id`, `estudiante_id`, `preguntas_asignadas` (lista de `PreguntaAsignada`, Value Object), `respuestas` (vacía en esta US), `estado` (`EnCurso`), `iniciada_en` |
| Value Object | `PreguntaAsignada` | `pregunta_id`, `orden` — sin identidad propia, fijado por completo en este comando |
| Command | `IniciarEvaluacion(actividad_id, estudiante_id)` | Crea la `Evaluacion`, o la retoma si ya existe una en curso (idempotente) |
| Domain Event | `EvaluacionIniciada` | Fija el set de `PreguntaAsignada` — único evento de esta US |
| Port (nuevo) | `EstudianteConsultaPort` → BC Identidad | Valida que `estudiante_id` existe y tiene rol Estudiante |

---

## Especificacion del comportamiento

### Precondicion

- Actor autenticado con JWT válido y claim `rol = estudiante`.
- `US-3.1.2` implementada — la `ActividadEvaluativaPeriodoAbierto` referenciada existe.
- `US-3.1.1` implementada (event store para el stream de `Evaluacion`, distinto del stream de
  `ActividadEvaluativaPeriodoAbierto` — dos aggregates, dos streams, `BC-actividad-evaluativa-modelo.md`
  §2).

### Postcondicion

- Si no existe una `Evaluacion` previa para `(actividad_id, estudiante_id)`: se crea una nueva,
  `preguntas_asignadas` sampleada al azar (`random.sample` sobre `PreguntaConsultaPort`,
  `cantidad_preguntas` de la actividad) y `estado = EnCurso`. Emite `EvaluacionIniciada`.
- Si ya existe una `Evaluacion` `EnCurso` para ese par: la operación es idempotente — devuelve
  la existente sin emitir un evento nuevo ni volver a samplear el set (INV-AE-05).
- Si existe una `Evaluacion` `Suspendida` o `Finalizada` para ese par: **no** aplica esta US —
  ver Fuera de alcance.

### Invariantes

| ID | Invariante |
|----|------------|
| INV-AE-05 | El set de `PreguntaAsignada` es fijo desde `EvaluacionIniciada` — un `IniciarEvaluacion` posterior sobre la misma `Evaluacion` `EnCurso` nunca genera un set nuevo. |
| INV-AE-06 | A lo sumo una `Evaluacion` en curso por `(actividad_id, estudiante_id)` — `IniciarEvaluacion` es idempotente si ya existe una `EnCurso`. |
| — (`FueraDePeriodo`) | Rechaza si `ahora` < `fecha_apertura`, o `ahora` > `fecha_cierre` vigente, o la actividad está `cerrada_manualmente`. |

---

## Criterios de aceptacion

```gherkin
Feature: Inicio de evaluación con set aleatorio (US-3.1.3)

  Scenario: Estudiante inicia su evaluación por primera vez
    Given una ActividadEvaluativaPeriodoAbierto vigente con cantidad_preguntas=10
    And un Estudiante autenticado sin Evaluacion previa para esa actividad
    When ejecuta IniciarEvaluacion(actividad_id, estudiante_id)
    Then el sistema crea una Evaluacion con estado EnCurso
    And preguntas_asignadas tiene exactamente 10 PreguntaAsignada
    And se emite el evento EvaluacionIniciada

  Scenario: Reconexión — idempotencia sin nuevo set
    Given una Evaluacion EnCurso ya existente para (actividad_id, estudiante_id)
    When el mismo Estudiante ejecuta IniciarEvaluacion(actividad_id, estudiante_id) de nuevo
    Then el sistema devuelve la misma Evaluacion existente
    And preguntas_asignadas es idéntico al set original (mismo orden, mismas preguntas)
    And no se emite un nuevo evento EvaluacionIniciada

  Scenario: Dos estudiantes reciben sets distintos
    Given una ActividadEvaluativaPeriodoAbierto vigente con más preguntas activas que
      cantidad_preguntas
    When dos Estudiantes distintos ejecutan IniciarEvaluacion cada uno por su cuenta
    Then cada uno recibe su propia Evaluacion con un set de preguntas propio

  Scenario: Rechazo antes de la apertura
    Given una ActividadEvaluativaPeriodoAbierto con fecha_apertura futura
    When un Estudiante ejecuta IniciarEvaluacion(actividad_id, estudiante_id)
    Then el sistema rechaza la operación con FueraDePeriodo

  Scenario: Rechazo después del cierre
    Given una ActividadEvaluativaPeriodoAbierto con fecha_cierre pasada
    When un Estudiante sin Evaluacion previa ejecuta IniciarEvaluacion(actividad_id, estudiante_id)
    Then el sistema rechaza la operación con FueraDePeriodo
```

---

## Fuera de alcance de esta US

- **Retomar una `Evaluacion` `Suspendida`** — es `ReanudarEvaluacion` (`US-3.2.2`, Iteración 2),
  comando distinto, no una variante de `IniciarEvaluacion`.
- **`RegistrarRespuesta`** sobre el set ya asignado — `US-3.2.1`, Iteración 2.
- Mostrar el set de preguntas al estudiante (pantalla de rendir) — `US-3.4.6`, Iteración 4. Esta
  US solo expone el endpoint que arma y persiste `Evaluacion`.

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — usa el event store de `US-3.1.1` y sampleo aleatorio dentro del propio Use Case
  (`random.sample`), mismo criterio de "no ensanchar puertos existentes" ya aplicado en
  `US-2.1.9` (`BC-actividad-evaluativa-modelo.md` §7).

**Capa(s) afectadas:**
- [x] Entities — `Evaluacion`, `PreguntaAsignada`, `EvaluacionIniciada`, `EstudianteConsultaPort`
  (`entities/ports/`)
- [x] Use Cases — `IniciarEvaluacionUseCase` (idempotencia INV-AE-06, sampleo RF-12, valida
  `FueraDePeriodo` contra la `ActividadEvaluativaPeriodoAbierto` cargada por replay)
- [x] Interface Adapters — `EvaluacionesController`, `EstudianteConsultaPortInProcess`
- [x] Frameworks — endpoint FastAPI `POST /evaluaciones` (requiere rol `estudiante`)
- [ ] Frontend — cubierto por `US-3.4.6` (Iteración 4)

---

## Fuente de verdad UX

No aplica a esta spec (backend puro) — la pantalla de rendir (`#est-rendir`) se especifica en
`US-3.4.6`, wireframe ya aprobado en `docs/design/ux/wireframes-actividad-evaluativa.md` §3.3.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/actividad_evaluativa/entities/evaluacion.py` | Aggregate `Evaluacion`, Value Object `PreguntaAsignada` |
| `src/actividad_evaluativa/entities/eventos.py` | `EvaluacionIniciada` (agrega al archivo de `US-3.1.2`) |
| `src/actividad_evaluativa/entities/errors.py` | `FueraDePeriodo` (agrega al archivo de `US-3.1.2`) |
| `src/actividad_evaluativa/entities/ports/estudiante_consulta_port.py` | Puerto nuevo — valida existencia y rol del estudiante |
| `src/actividad_evaluativa/use_cases/iniciar_evaluacion.py` | Orquesta INV-AE-05/06, sampleo aleatorio (RF-12), valida `FueraDePeriodo` |
| `src/actividad_evaluativa/interface_adapters/controllers/evaluaciones_controller.py` | Validación de entrada, mapeo a use case |
| `src/actividad_evaluativa/frameworks/adapters/estudiante_consulta_port_in_process.py` | Implementación — llama a BC Identidad |
| `src/actividad_evaluativa/frameworks/api/evaluaciones_router.py` | Endpoint `POST /evaluaciones` |
| `src/actividad_evaluativa/frameworks/dependencies.py` | Registra el nuevo use case y su adapter |

---

## Referencias

- Depende de: `US-3.1.1` (event store), `US-3.1.2` (actividad a la que se inicia una evaluación)
- Relacionada con: `US-3.2.1` (registra respuestas sobre el set fijado aquí), `US-3.2.2`
  (`ReanudarEvaluacion`, distinto de la idempotencia de esta US)
- Modelo de dominio: `docs/design/domain/BC-actividad-evaluativa-modelo.md` §3, §4, §5
  (`Evaluacion`, `PreguntaAsignada`), §7 (puertos, sampleo aleatorio)
- Candidatas: `docs/plans/inc3/inc3-candidatas.md`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
