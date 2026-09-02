# US-3.2.2: Estudiante suspende y reanuda su evaluación

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-3.2`
**Tipo**: `feat backend`
**Agregado principal afectado**: `Evaluacion`
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Estudiante**,
quiero **pausar mi evaluación de forma explícita y reanudarla más tarde**
para **interrumpirla deliberadamente sin perder mis respuestas, dejando registrado que fue una
pausa consciente y no una simple desconexión**.

---

## Contexto del dominio

### Problema

`US-3.1.3` fija el set de preguntas al iniciar y `US-3.2.1` persiste cada respuesta al
instante — ambos ya toleran una reconexión simple (retoma la `Evaluacion` `EnCurso` sin generar
nada nuevo). Falta el mecanismo *deliberado*: el estudiante decide pausar (no una caída de red),
queda registrado como hecho de dominio (`EvaluacionSuspendida`, trazabilidad — RNF
Observabilidad), y mientras dura la pausa `RegistrarRespuesta` se rechaza (INV-AE-12, ya
implementado en `US-3.2.1` — `EvaluacionSuspendida` no es un error nuevo). Esta US agrega las
dos transiciones que faltan al ciclo de vida de `Evaluacion`: `EnCurso → Suspendida` y
`Suspendida → EnCurso`. Habilita a `US-3.2.4` (`VerificadorDeVencimientos`, Regla 1) a disparar
`SuspenderEvaluacion` con actor `Sistema` reutilizando el mismo Use Case tal cual.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Aggregate (existente) | `Evaluacion` | Gana las transiciones `suspender()`/`reanudar()` sobre `estado` |
| Command | `SuspenderEvaluacion(evaluacion_id)` | `EnCurso → Suspendida` |
| Command | `ReanudarEvaluacion(evaluacion_id)` | `Suspendida → EnCurso` |
| Domain Event | `EvaluacionSuspendida` | Hecho de dominio — mismo evento sin importar el actor (estudiante o, más adelante, `Sistema` en `US-3.2.4`); el payload distingue `actor` |
| Domain Event | `EvaluacionReanudada` | Vuelve a `EnCurso`, mismo set y `respuestas` — no genera ninguna `Respuesta` ni cambia `preguntas_asignadas` |

Esta US implementa solo el actor `Estudiante`, explícito vía HTTP. El campo `actor` del payload
de `EvaluacionSuspendida` ya se incluye (valor fijo `"estudiante"`) para no romper el esquema
del evento cuando `US-3.2.4` agregue el disparo automático con `actor = "sistema"`.

---

## Especificacion del comportamiento

### Precondicion

- Actor autenticado con JWT válido y claim `rol = estudiante`.
- `US-3.1.3`/`US-3.2.1` implementadas — existe una `Evaluacion` para `evaluacion_id`,
  perteneciente al estudiante autenticado.

### Postcondicion

**`SuspenderEvaluacion`:**
- `Evaluacion.estado` pasa de `EnCurso` a `Suspendida`.
- Evento `EvaluacionSuspendida` persistido en el stream de la `Evaluacion`.
- `respuestas` y `preguntas_asignadas` no se modifican.

**`ReanudarEvaluacion`:**
- `Evaluacion.estado` pasa de `Suspendida` a `EnCurso`.
- Evento `EvaluacionReanudada` persistido en el stream de la `Evaluacion`.
- El estudiante puede volver a `RegistrarRespuesta` de inmediato, mismo set y `respuestas`
  previas intactas.

### Invariantes

| ID | Invariante |
|----|------------|
| INV-AE-11 | `ReanudarEvaluacion` solo es válido sobre una `Evaluacion` `Suspendida` — `EvaluacionYaFinalizada` si está `Finalizada`, `EvaluacionNoSuspendida` si está `EnCurso` (no hay nada que reanudar). |
| INV-AE-12 | `SuspenderEvaluacion` solo es válido sobre una `Evaluacion` `EnCurso` — `EvaluacionYaSuspendida` si ya está `Suspendida`, `EvaluacionYaFinalizada` si está `Finalizada`. (`RegistrarRespuesta` sobre `Suspendida` ya rechaza con `EvaluacionSuspendida` desde `US-3.2.1` — sin cambios acá.) |
| — (`FueraDePeriodo`) | `ReanudarEvaluacion` rechaza si la actividad ya no está dentro de su período vigente (`fecha_apertura` ≤ ahora ≤ `fecha_cierre`, incluida cualquier extensión de `US-3.3.1`) — mismo criterio que `IniciarEvaluacion`/`RegistrarRespuesta`. `SuspenderEvaluacion` **no** valida período: pausar siempre debe poder hacerse, incluso si el período ya venció (la revalidación de vigencia ocurre recién al intentar reanudar o registrar respuesta). |
| — (`EvaluacionNoExiste`) | Ambos comandos rechazan si `evaluacion_id` no corresponde a ninguna `Evaluacion` existente, o no pertenece al estudiante autenticado. |

---

## Criterios de aceptacion

```gherkin
Feature: Suspensión y reanudación explícita de la evaluación (US-3.2.2)

  Scenario: Estudiante suspende una evaluación en curso
    Given una Evaluacion EnCurso
    When el Estudiante ejecuta SuspenderEvaluacion(evaluacion_id)
    Then el estado pasa a Suspendida
    And se emite el evento EvaluacionSuspendida

  Scenario: Estudiante reanuda una evaluación suspendida
    Given una Evaluacion Suspendida con respuestas ya registradas
    When el Estudiante ejecuta ReanudarEvaluacion(evaluacion_id)
    Then el estado pasa a EnCurso
    And se emite el evento EvaluacionReanudada
    And las respuestas y el set de preguntas asignadas no cambian

  Scenario: Reanudar habilita volver a registrar respuestas
    Given una Evaluacion recién reanudada
    When el Estudiante confirma una respuesta
    Then el sistema la registra normalmente (sin EvaluacionSuspendida)

  Scenario: Rechazo al suspender una evaluación ya suspendida
    Given una Evaluacion Suspendida
    When el Estudiante intenta SuspenderEvaluacion de nuevo
    Then el sistema rechaza la operación con EvaluacionYaSuspendida

  Scenario: Rechazo al suspender una evaluación finalizada
    Given una Evaluacion Finalizada
    When el Estudiante intenta SuspenderEvaluacion
    Then el sistema rechaza la operación con EvaluacionYaFinalizada

  Scenario: Rechazo al reanudar una evaluación en curso
    Given una Evaluacion EnCurso
    When el Estudiante intenta ReanudarEvaluacion
    Then el sistema rechaza la operación con EvaluacionNoSuspendida

  Scenario: Rechazo al reanudar una evaluación finalizada
    Given una Evaluacion Finalizada
    When el Estudiante intenta ReanudarEvaluacion
    Then el sistema rechaza la operación con EvaluacionYaFinalizada

  Scenario: Rechazo al reanudar fuera del período vigente
    Given una Evaluacion Suspendida cuya actividad ya pasó su fecha_cierre
    When el Estudiante intenta ReanudarEvaluacion
    Then el sistema rechaza la operación con FueraDePeriodo

  Scenario: Suspender no valida período vigente
    Given una Evaluacion EnCurso cuya actividad ya pasó su fecha_cierre
    When el Estudiante ejecuta SuspenderEvaluacion
    Then el sistema acepta la operación y el estado pasa a Suspendida
```

---

## Fuera de alcance de esta US

- **Disparo automático por inactividad (Regla 1 del `VerificadorDeVencimientos`)** —
  `US-3.2.4`, reutiliza `SuspenderEvaluacion` tal cual con actor `Sistema`.
- **Finalizar la evaluación** — `US-3.2.3`.
- **Pantalla de pausa/reanudación** — `US-3.4.6` (Iteración 4). Esta US solo expone los
  endpoints.

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — usa el event store de `US-3.1.1`, la Unit of Work por Use Case (`ADR-009`) y el
  mismo patrón de replay/append de `US-3.1.3`/`US-3.2.1`. `EvaluacionesController` pasa de 2 a
  4 Use Case inyectados — vigilar el umbral de CBO en el pre-push gate (mismo patrón repetido
  en Incremento 2 con `PreguntasController`/`CuentasController`); si se dispara, separar por
  command/query o mover a un controller propio, no forzar el diseño previamente.

**Capa(s) afectadas:**
- [x] Entities — métodos `Evaluacion.suspender()`/`reanudar()` (aplican INV-AE-11/12 sobre el
  estado ya cargado), eventos `EvaluacionSuspendida`/`EvaluacionReanudada`, errores
  `EvaluacionYaSuspendida`/`EvaluacionNoSuspendida`, actualiza `reconstruir` para reproducir
  ambos eventos sobre `estado`
- [x] Use Cases — `SuspenderEvaluacionUseCase`, `ReanudarEvaluacionUseCase` (cargan `Evaluacion`
  por replay, validan invariantes, arman el evento, invocan `EventStorePort.append` con
  concurrencia optimista; `ReanudarEvaluacionUseCase` también carga la actividad para validar
  `FueraDePeriodo`)
- [x] Interface Adapters — extiende `EvaluacionesController` con `suspender_evaluacion`/
  `reanudar_evaluacion`
- [x] Frameworks — endpoints FastAPI `POST /evaluaciones/{evaluacion_id}/suspender` y
  `POST /evaluaciones/{evaluacion_id}/reanudar` (rol `estudiante`)
- [ ] Frontend — cubierto por `US-3.4.6` (Iteración 4)

---

## Fuente de verdad UX

No aplica a esta spec (backend puro) — la pantalla de rendir con pausa/reanudación
(`#est-suspendida`) se especifica en `US-3.4.6`, wireframe ya aprobado en
`docs/design/ux/wireframes-actividad-evaluativa.md` §3.4.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/actividad_evaluativa/entities/evaluacion.py` | Métodos `suspender()`/`reanudar()` (INV-AE-11/12), actualiza `reconstruir` para reproducir `EvaluacionSuspendida`/`EvaluacionReanudada` sobre `estado` |
| `src/actividad_evaluativa/entities/eventos.py` | `EvaluacionSuspendida`, `EvaluacionReanudada` (agrega al archivo existente) |
| `src/actividad_evaluativa/entities/errors.py` | `EvaluacionYaSuspendida`, `EvaluacionNoSuspendida` |
| `src/actividad_evaluativa/use_cases/suspender_evaluacion.py` | Orquesta INV-AE-12, invoca `EventStorePort.append` |
| `src/actividad_evaluativa/use_cases/reanudar_evaluacion.py` | Orquesta INV-AE-11 + `FueraDePeriodo` (carga actividad), invoca `EventStorePort.append` |
| `src/actividad_evaluativa/interface_adapters/controllers/evaluaciones_controller.py` | Métodos nuevos `suspender_evaluacion`/`reanudar_evaluacion`, dos Use Case más inyectados |
| `src/actividad_evaluativa/frameworks/api/evaluaciones_router.py` | Endpoints `POST /evaluaciones/{evaluacion_id}/suspender` y `.../reanudar` |
| `src/actividad_evaluativa/frameworks/dependencies.py` | Registra los dos Use Case nuevos |

---

## Referencias

- Depende de: `US-3.1.1` (event store), `US-3.1.3` (`Evaluacion` existente), `US-3.2.1`
  (`EvaluacionSuspendida` ya usado como error de `RegistrarRespuesta`, INV-AE-12)
- Relacionada con: `US-3.2.3` (finalizar puede ocurrir desde `Suspendida`), `US-3.2.4`
  (`VerificadorDeVencimientos` reutiliza `SuspenderEvaluacion` con actor `Sistema`, Regla 1)
- Modelo de dominio: `docs/design/domain/BC-actividad-evaluativa-modelo.md` §3 (comandos),
  §4 (tabla comando→evento), §5 (`Evaluacion`, INV-AE-11/12), §6b (`VerificadorDeVencimientos`,
  contexto de por qué el evento lleva `actor`)
- Candidatas: `docs/plans/inc3/inc3-candidatas.md`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
