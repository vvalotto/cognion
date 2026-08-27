# US-3.2.4: VerificadorDeVencimientos — suspensión y finalización automáticas

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-3.2`
**Tipo**: `feat backend (técnica)`
**Agregado principal afectado**: `Evaluacion` (vía los Use Case existentes, sin invariantes nuevas)
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Sistema**,
quiero **disparar automáticamente lo que un actor humano no disparó a tiempo** —suspender una
`Evaluacion` inactiva y finalizar una `Evaluacion` cuya actividad ya venció—
para **que ninguna evaluación quede indefinidamente `EnCurso` sin actividad, ni sobreviva
pasivamente al cierre del período (RNF Confiabilidad)**.

---

## Contexto del dominio

### Problema

`US-3.2.2`/`US-3.2.3` dejan `SuspenderEvaluacion`/`FinalizarEvaluacion` disponibles solo como
acción explícita del Estudiante. Falta el disparador automático que `BC-actividad-evaluativa-
modelo.md` §6b describe como `VerificadorDeVencimientos`: una Policy/Process Manager (no un
aggregate) que reacciona al paso del tiempo, no a un comando humano, y reutiliza los dos Use
Case existentes sin agregarles invariantes nuevas. Cierra la Iteración 2 del Incremento 3
(backend) — a partir de esta US, ninguna `Evaluacion` puede quedar indefinidamente activa sin
que algo la mueva a un estado terminal o de pausa.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Policy (nuevo, no aggregate) | `VerificarVencimientosUseCase` | Orquesta las Reglas 1 y 2 sobre todas las `Evaluacion` no `Finalizada`, reutilizando `SuspenderEvaluacionUseCase`/`FinalizarEvaluacionUseCase` |
| Port de query (nuevo) | `EvaluacionActivaQueryPort` | Resumen `(evaluacion_id, actividad_id, estado, ultima_actividad_en)` de toda `Evaluacion` no `Finalizada` — CQRS, separado del `EventStorePort` de escritura/replay por stream |
| Use Case (existente, extendido) | `SuspenderEvaluacionUseCase`/`FinalizarEvaluacionUseCase` | Ganan un modo de invocación con `actor="sistema"`, sin `estudiante_id` (ver "Decisiones de diseño") |
| Domain Event (existente, sin cambios de esquema) | `EvaluacionSuspendida`/`EvaluacionFinalizada` | Mismo hecho de dominio, `payload["actor"] = "sistema"` en vez de `"estudiante"` |

Regla 3 (cascada síncrona de `CerrarActividad`) **no** es parte de esta US — pertenece a
`US-3.3.2` (Iteración 3), que reutilizará `FinalizarEvaluacionUseCase` con el mismo mecanismo de
actor `sistema` introducido acá.

---

## Especificacion del comportamiento

### Precondicion

- `US-3.1.1` a `US-3.2.3` implementadas — existen `Evaluacion` con eventos persistidos en el
  event store del BC.
- Sin actor HTTP: este Use Case no se invoca vía JWT/rol — corre como proceso interno del
  Sistema (ver "Disparador" más abajo).

### Postcondicion

- Toda `Evaluacion` `EnCurso` sin actividad por más de `UMBRAL_INACTIVIDAD` pasa a `Suspendida`
  vía `EvaluacionSuspendida` (`actor = "sistema"`).
- Toda `Evaluacion` `EnCurso`/`Suspendida` de una actividad con `fecha_cierre` ya pasada (y no
  cerrada manualmente) pasa a `Finalizada` vía `EvaluacionFinalizada` (`actor = "sistema"`).
- Repetir la corrida sobre una `Evaluacion` que ya cambió de estado por esta misma vía o por
  acción manual del estudiante es un no-op silencioso — no levanta error, no reemite evento.

### Invariantes

| ID | Invariante |
|----|------------|
| INV-AE-11 (reutilizada) | Solo se reanuda/finaliza una `Evaluacion` no `Finalizada` — protege la Regla 2 de reintentar sobre lo ya terminal. |
| INV-AE-12 (reutilizada) | `RegistrarRespuesta` sigue exigiendo `EnCurso` — una `Evaluacion` suspendida por la Policy queda protegida igual que si la hubiera suspendido el Estudiante. |
| — (nueva, a nivel Use Case, no aggregate) | Cuando el actor es `"sistema"`, `EvaluacionYaSuspendida`/`EvaluacionYaFinalizada` se capturan dentro del propio Use Case y no se propagan — es el "no-op silencioso" que describe `BC-actividad-evaluativa-modelo.md` §6b, a diferencia del pedido manual del Estudiante, que sí ve el error como feedback de UI. |

### Decisiones de diseño (no cubiertas literalmente por el modelo o el Issue #159)

1. **Extensión de `SuspenderEvaluacionUseCase`/`FinalizarEvaluacionUseCase`, no reuso literal
   "tal cual".** El Issue y el modelo dicen que la Policy "reutiliza…tal cual", pero el código
   actual (`US-3.2.2`/`US-3.2.3`) exige `estudiante_id` para el chequeo de pertenencia y fija
   `actor="estudiante"` hardcodeado en el evento — la Policy no tiene un `estudiante_id` de
   contexto (no viene de un request autenticado). Se extiende la firma de `execute()` a
   `execute(evaluacion_id, estudiante_id=None, *, actor="estudiante")`: con `actor="estudiante"`
   (default) el comportamiento es exactamente el de hoy, sin tocar ningún caller HTTP existente;
   con `actor="sistema"` se omite el chequeo de pertenencia (la Policy ya seleccionó
   `evaluacion_id` desde el read model, no hay usuario que impersonar) y los errores de estado
   ya alcanzado se capturan como no-op en vez de propagarse. Es la extensión mínima que preserva
   el 100% del comportamiento y los tests existentes de `US-3.2.2`/`US-3.2.3`.
2. **Read model como proyección de lectura sobre `events`, no una tabla sincronizada aparte.**
   `BC-actividad-evaluativa-modelo.md` §6b sugiere una tabla `evaluaciones_activas_por_actividad`
   actualizada síncronamente en la transacción de cada evento — eso exigiría tocar los 4 Use
   Case ya cerrados y en producción de pruebas (`US-3.1.3`/`US-3.2.1`/`US-3.2.2`/`US-3.2.3`) y
   una migración nueva. A esta escala (30-60 alumnos, el propio §6b lo admite: "no justifica un
   mecanismo más fino que polling") se implementa como una **query de lectura** directa sobre la
   tabla `events` existente (agrupada por `aggregate_id`, sin persistencia adicional): mismo
   contrato observable (`EvaluacionActivaQueryPort.listar_no_finalizadas()`), cero riesgo de que
   el read model se desincronice de los Use Case existentes, sin migración nueva. **Confirmado
   con Víctor 2026-08-27** — se implementa la query de lectura, no la tabla sincronizada.
3. **Disparador — `asyncio` en background, no un scheduler externo.** El proyecto no tiene
   APScheduler/Celery (`pyproject.toml`). Se implementa como una tarea de background nativa de
   `asyncio` (`asyncio.create_task` en el startup de `src/app.py`, `while True: ejecutar() ;
   await asyncio.sleep(CADENCIA_SEGUNDOS)`), sin dependencia nueva — alternativa de "menor
   infraestructura" que el propio `BC-actividad-evaluativa-modelo.md` §6b valida como mismo
   criterio que un job periódico. **Confirmado con Víctor 2026-08-27:** `CADENCIA_SEGUNDOS = 120`
   (2 minutos), `UMBRAL_INACTIVIDAD = 15 minutos` — ambos como parámetros de configuración
   (settings), no constantes de dominio ni invariantes.
4. **`ActividadEvaluativaPeriodoAbierto` sin `reconstruir()` todavía.** `US-3.3.1`
   (`ModificarPeriodoDisponibilidad`) y `US-3.3.2` (`CerrarActividad`) — que agregarían más
   eventos al stream de la actividad — son Iteración 3, no implementadas todavía. Por ahora el
   stream de cada actividad tiene un único evento (`ActividadEvaluativaCreada`), así que la
   Regla 2 lee `fecha_cierre` directamente de ese evento y asume `cerrada_manualmente = False`
   (no hay otro valor posible hoy). Cuando `US-3.3.1`/`US-3.3.2` implementen `reconstruir()`
   sobre este aggregate, la Regla 2 deberá cambiar a reconstruir el stream completo en vez de
   leer el primer evento — se deja como nota para esa US, no bloquea esta implementación.

---

## Criterios de aceptacion

```gherkin
Feature: VerificadorDeVencimientos - suspension y finalizacion automaticas (US-3.2.4)

  Scenario: Regla 1 suspende una Evaluacion inactiva
    Given una Evaluacion EnCurso cuya ultima_actividad_en supera el UMBRAL_INACTIVIDAD
    When se ejecuta VerificarVencimientosUseCase
    Then la Evaluacion pasa a Suspendida
    And se emite EvaluacionSuspendida con actor "sistema"

  Scenario: Regla 1 no afecta una Evaluacion EnCurso con actividad reciente
    Given una Evaluacion EnCurso cuya ultima_actividad_en es menor al UMBRAL_INACTIVIDAD
    When se ejecuta VerificarVencimientosUseCase
    Then la Evaluacion sigue EnCurso
    And no se emite ningun evento nuevo

  Scenario: Regla 2 finaliza una Evaluacion EnCurso de una actividad vencida
    Given una ActividadEvaluativaPeriodoAbierto con fecha_cierre en el pasado
    And una Evaluacion EnCurso de esa actividad
    When se ejecuta VerificarVencimientosUseCase
    Then la Evaluacion pasa a Finalizada
    And se emite EvaluacionFinalizada con actor "sistema"

  Scenario: Regla 2 finaliza una Evaluacion Suspendida de una actividad vencida
    Given una ActividadEvaluativaPeriodoAbierto con fecha_cierre en el pasado
    And una Evaluacion Suspendida de esa actividad
    When se ejecuta VerificarVencimientosUseCase
    Then la Evaluacion pasa a Finalizada

  Scenario: Regla 2 no afecta evaluaciones de una actividad todavia vigente
    Given una ActividadEvaluativaPeriodoAbierto con fecha_cierre en el futuro
    And una Evaluacion EnCurso de esa actividad
    When se ejecuta VerificarVencimientosUseCase
    Then la Evaluacion sigue EnCurso

  Scenario: Idempotencia - segunda corrida sobre lo ya procesado es un no-op
    Given una Evaluacion que ya fue Suspendida por una corrida anterior de VerificarVencimientosUseCase
    When se ejecuta VerificarVencimientosUseCase de nuevo
    Then la Evaluacion sigue Suspendida
    And no se levanta ninguna excepcion
    And no se emite un segundo EvaluacionSuspendida

  Scenario: Evaluacion ya Finalizada nunca se reconsidera
    Given una Evaluacion Finalizada
    When se ejecuta VerificarVencimientosUseCase
    Then la Evaluacion no aparece en el resultado de EvaluacionActivaQueryPort.listar_no_finalizadas
```

---

## Fuera de alcance de esta US

- **Regla 3 (cascada síncrona de `CerrarActividad`)** — `US-3.3.2`, Iteración 3.
- **`ModificarPeriodoDisponibilidad`/reconstrucción completa del stream de
  `ActividadEvaluativaPeriodoAbierto`** — `US-3.3.1`, Iteración 3 (ver Decisión de diseño 4).
- **Endpoint HTTP o pantalla para disparar o visualizar la corrida manualmente** — la Policy
  corre exclusivamente en background; no hay caso de uso de negocio que la exponga por HTTP en
  este incremento.
- **Notificación al estudiante/docente de la suspensión o finalización automática** — BC
  Notificaciones, fuera de este incremento (`RF_v1.md`).

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] Sí, menor — dos decisiones locales documentadas arriba (extensión de firma de los Use
  Case existentes con `actor`/`estudiante_id` opcional; read model como query de lectura en vez
  de tabla sincronizada) que no rompen ningún test ni endpoint existente, y una decisión de
  infraestructura (background task de `asyncio`, sin dependencia nueva) — no amerita ADR
  (`ARQ_v1.md`) por ser reversible y acotado a este BC, mismo umbral aplicado en decisiones
  similares de Incremento 2/3.

**Capa(s) afectadas:**
- [x] Entities/Ports — `EvaluacionActivaQueryPort` (nuevo) + VO `EvaluacionActivaResumen`
- [x] Use Cases — `SuspenderEvaluacionUseCase`/`FinalizarEvaluacionUseCase` extienden `execute()`
  con `estudiante_id: UUID | None = None, *, actor: str = "estudiante"`, capturando
  `EvaluacionYaSuspendida`/`EvaluacionYaFinalizada` como no-op cuando `actor == "sistema"`; Use
  Case nuevo `VerificarVencimientosUseCase` (orquesta Reglas 1 y 2, sin comando ni evento
  propio — invoca los dos anteriores)
- [x] Frameworks — `SQLAlchemyEvaluacionActivaQueryRepository` (implementa el nuevo port
  agrupando `EventoModel` por `aggregate_id`, sin tabla nueva); tarea de background en
  `src/app.py` (startup event) que instancia `VerificarVencimientosUseCase` cada
  `CADENCIA_SEGUNDOS` dentro de su propia sesión/Unit of Work por corrida; `CADENCIA_SEGUNDOS`/
  `UMBRAL_INACTIVIDAD` como settings (`pydantic-settings`, mismo mecanismo que el resto de la
  configuración del proyecto)
- [ ] Interface Adapters — no aplica, sin controller ni endpoint HTTP (ver "Fuera de alcance")
- [ ] Frontend — no aplica a esta US (Iteración 4 no expone esta Policy directamente)

---

## Fuente de verdad UX

No aplica — sin pantalla ni endpoint HTTP, es un proceso interno del Sistema.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/actividad_evaluativa/entities/ports/evaluacion_activa_query_port.py` | Nuevo — `EvaluacionActivaQueryPort`, VO `EvaluacionActivaResumen` |
| `src/actividad_evaluativa/use_cases/suspender_evaluacion.py` | `execute()` gana `estudiante_id: UUID \| None = None, *, actor: str = "estudiante"`; captura no-op cuando `actor == "sistema"` |
| `src/actividad_evaluativa/use_cases/finalizar_evaluacion.py` | Mismo cambio que `suspender_evaluacion.py` |
| `src/actividad_evaluativa/use_cases/verificar_vencimientos.py` | Nuevo — `VerificarVencimientosUseCase`, orquesta Reglas 1 y 2 |
| `src/actividad_evaluativa/frameworks/adapters/evaluacion_activa_query_repository.py` | Nuevo — implementación SQLAlchemy del port, agrupa `EventoModel` en memoria |
| `src/actividad_evaluativa/frameworks/dependencies.py` | Función de fábrica para `VerificarVencimientosUseCase` (con su propia sesión/UoW, no vía `Depends` de FastAPI — corre fuera del ciclo request/response) |
| `src/actividad_evaluativa/frameworks/config.py` (o `src/shared/frameworks/settings.py` si ya existe un settings compartido) | `CADENCIA_VERIFICADOR_SEGUNDOS`, `UMBRAL_INACTIVIDAD_MINUTOS` |
| `src/app.py` | `@app.on_event("startup")` (o `lifespan`) lanza el background task; se cancela en shutdown |

---

## Referencias

- Depende de: `US-3.1.1` (event store), `US-3.1.2`/`US-3.1.3` (`ActividadEvaluativaPeriodoAbierto`/`Evaluacion` existentes), `US-3.2.1` (`RespuestaRegistrada` alimenta `ultima_actividad_en`), `US-3.2.2` (`SuspenderEvaluacionUseCase`), `US-3.2.3` (`FinalizarEvaluacionUseCase`)
- Relacionada con: `US-3.3.1`/`US-3.3.2` (Iteración 3 — reutilizarán el mecanismo de actor `sistema` introducido acá; `US-3.3.2` en particular para la Regla 3)
- Modelo de dominio: `docs/design/domain/BC-actividad-evaluativa-modelo.md` §6 (event store, read models), §6b (`VerificadorDeVencimientos`, Reglas 1/2/3)
- Candidatas: `docs/plans/inc3/inc3-candidatas.md` (Iteración 2)
- Issue: [#159](https://github.com/vvalotto/cognion/issues/159)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
