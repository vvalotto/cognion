# US-6.1.2: Docente crea una sesión en vivo desde el detalle de una Comisión

**Estado**: `Implementada`
**Iteracion / Sprint**: `INC-6.1`
**Tipo**: `feature backend`
**Agregado principal afectado**: `ActividadEvaluativaEnVivo`
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **crear una sesión en vivo para una Comisión puntual, indicando cuántas preguntas y
cuánto tiempo por pregunta**,
para **arrancarla en clase con el set de preguntas ya fijado de antemano, igual para todos los
que se unan**.

---

## Contexto del dominio

### Problema

Primer comando del agregado `ActividadEvaluativaEnVivo` (RF-08) — construye el aggregate raíz
de la sesión en el estado inicial `EnEspera`, con el set de preguntas ya sampleado al azar
(mismo criterio que `EvaluacionIniciada`, RF-12, `US-3.1.3`) pero fijado **al crear la sesión**,
no al iniciarla — a diferencia del modo período abierto, acá no hay ambigüedad de "quién lo
dispara": es un único comando del Docente, sin un estudiante de por medio todavía.

Diferencia central respecto de `CrearActividadPeriodoAbierto` (`US-3.1.2`): el comando recibe
`comision_id`, no `materia_id` — el Docente entra primero al detalle de una Comisión concreta
(`ComisionDetalleDocente.tsx`, ya existente) y desde ahí crea la sesión (`BC-actividad-evaluativa-modelo.md`
§17 punto 11). `materia_id` se resuelve internamente vía `ComisionConsultaPort` (`US-6.1.1`).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Aggregate (nuevo) | `ActividadEvaluativaEnVivo` | Root del modo en vivo — `id`, `comision_id`, `materia_id`, `unidad_tematica`/`tema`, `preguntas` (`PreguntaAsignada`, VO ya existente), `tiempo_limite_por_pregunta_segundos`, `estado`, `pregunta_actual_indice`, `opciones_mostradas`, `pregunta_actual_cerrada` (`BC-actividad-evaluativa-modelo.md` §14) — esta US solo ejercita la construcción inicial (`estado=EnEspera`, `pregunta_actual_indice=None`) |
| Comando | `CrearSesionEnVivo(comision_id, unidad_tematica, tema, cantidad_preguntas, tiempo_limite_por_pregunta_segundos)` | `unidad_tematica`/`tema` opcionales |
| Evento | `SesionEnVivoCreada` | Payload: `sesion_id`, `comision_id`, `materia_id`, `unidad_tematica`, `tema`, `preguntas` (lista de `PreguntaAsignada`), `tiempo_limite_por_pregunta_segundos` |
| Use Case (nuevo) | `CrearSesionEnVivoUseCase` | Resuelve `materia_id` (`ComisionConsultaPort`), samplea el set de preguntas (`PreguntaConsultaPort`, ya existente — reutilizado tal cual de `US-3.1.2`/`US-3.1.3`), construye el aggregate y hace `append` del primer evento de su stream |
| Controller (nuevo) | `SesionesEnVivoController` | `crear(comando) -> SesionEnVivoCreada` |
| Endpoint (nuevo) | `POST /sesiones-en-vivo` | Rol `docente` |

---

## Especificacion del comportamiento

### Precondicion

- `US-6.1.1` cerrada (infraestructura de tiempo real y `ComisionConsultaPort` disponibles —
  aunque esta US no publica todavía ningún mensaje por WebSocket, ver nota de alcance abajo).
- La Comisión existe (`ComisionConsultaPort.obtener_materia_id`) y tiene `Banco` con preguntas
  activas suficientes que matchean `materia_id`/`unidad_tematica`/`tema`.
- Docente autenticado.

### Postcondicion

- `ActividadEvaluativaEnVivo` persistida como primer evento (`sequence_number=1`) de su stream
  `(aggregate_type="ActividadEvaluativaEnVivo", aggregate_id=sesion_id)`.
- `estado = EnEspera`, `pregunta_actual_indice = None`, `opciones_mostradas = False`,
  `pregunta_actual_cerrada = False`.
- `preguntas` fijado en cantidad y orden desde este momento — inmutable en adelante (RF-08,
  "todos reciben el mismo set").
- Respuesta HTTP `201` con el `sesion_id` creado y el resumen de la sesión (sin las preguntas
  completas — el Docente ya las conoce del banco; se exponen recién al presentarlas, `US-6.1.4`
  y la Iteración 2).

**Nota de alcance — sin broadcast en esta US.** `SesionEnVivoCreada` no tiene un mensaje
asociado en la tabla de `BC-actividad-evaluativa-modelo.md` §16 (la sala de espera se sostiene
con el read model `participantes_por_sesion` de `US-6.1.3`, no con un mensaje de creación) — no
hay ningún estudiante conectado al canal todavía en este punto del flujo.

### Invariantes

| ID | Invariante |
|----|------------|
| INV-AEV-01 | `cantidad_preguntas` ≤ cantidad de `PreguntaPlantilla` activas que matchean `materia_id`/`unidad_tematica`/`tema` al momento de crear la sesión — mismo criterio que INV-AE-01. Si no alcanza: `PreguntasInsuficientes`. |
| INV-AEV-02 | `tiempo_limite_por_pregunta_segundos` > 0 — si no: `TiempoLimiteInvalido`. |

---

## Criterios de aceptacion

```gherkin
Feature: Docente crea una sesión en vivo (US-6.1.2)

  Scenario: Creación exitosa
    Given una Comisión existente cuya Materia tiene un Banco con preguntas activas suficientes
    When el Docente crea una sesión en vivo con cantidad_preguntas=10 y tiempo_limite_por_pregunta_segundos=30
    Then la sesión queda en estado EnEspera con 10 preguntas fijadas al azar
    And la respuesta HTTP es 201 con el sesion_id creado

  Scenario: Preguntas insuficientes en el banco
    Given una Comisión cuya Materia tiene un Banco con solo 5 preguntas activas
    When el Docente intenta crear una sesión en vivo con cantidad_preguntas=10
    Then el sistema rechaza la operación con PreguntasInsuficientes (422)
    And no se crea ninguna sesión

  Scenario: Tiempo límite inválido
    Given una Comisión con preguntas suficientes
    When el Docente intenta crear una sesión en vivo con tiempo_limite_por_pregunta_segundos=0
    Then el sistema rechaza la operación con TiempoLimiteInvalido (422)

  Scenario: Comisión inexistente
    Given un comision_id que no corresponde a ninguna Comisión
    When el Docente intenta crear una sesión en vivo
    Then el sistema rechaza la operación con ComisionNoExiste (404)

  Scenario: Rechazo por rol
    Given un usuario autenticado con rol Estudiante
    When intenta crear una sesión en vivo
    Then el sistema responde 403
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — construye el primer aggregate del modo en vivo siguiendo el patrón ya validado en
  `US-3.1.2` (mismo Event Sourcing, mismo `PreguntaConsultaPort`), con la única variación de
  resolver `materia_id` vía el `ComisionConsultaPort` nuevo de `US-6.1.1`.

**Capa(s) afectadas:**
- [x] Entities — `ActividadEvaluativaEnVivo` (aggregate), `SesionEnVivoCreada` (evento),
  `PreguntasInsuficientes`/`TiempoLimiteInvalido`/`ComisionNoExiste` (errores, algunos ya
  existentes)
- [x] Use Cases — `CrearSesionEnVivoUseCase`
- [x] Interface Adapters — `SesionesEnVivoController`
- [x] Frameworks — endpoint `POST /sesiones-en-vivo` en `sesiones_en_vivo_router.py`
  (`US-6.1.1`), wiring en `dependencies.py`
- [ ] Frontend — diferido, mismo criterio que la Iteración 1 del Incremento 3

---

## Fuente de verdad UX

No aplica a esta US — backend puro. La pantalla correspondiente (entry point "+ Nueva sesión en
vivo" desde `ComisionDetalleDocente.tsx`) está en
`docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md` §1.0, pendiente de iteración de
frontend (sin asignar todavía en `inc6-candidatas.md`).

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/actividad_evaluativa/entities/actividad_evaluativa_en_vivo.py` | Aggregate `ActividadEvaluativaEnVivo` — constructor/factory `crear(...)`, atributos de §14 |
| `src/actividad_evaluativa/entities/eventos_en_vivo.py` | `SesionEnVivoCreada` (dataclass de evento de dominio) |
| `src/actividad_evaluativa/entities/errors.py` | `TiempoLimiteInvalido`, `ComisionNoExiste` (si no existen ya con ese nombre) |
| `src/actividad_evaluativa/use_cases/crear_sesion_en_vivo.py` | `CrearSesionEnVivoUseCase` |
| `src/actividad_evaluativa/interface_adapters/controllers/sesiones_en_vivo_controller.py` | `SesionesEnVivoController.crear(...)` |
| `src/actividad_evaluativa/frameworks/api/sesiones_en_vivo_router.py` | `POST /sesiones-en-vivo` (rol `docente`) |
| `src/actividad_evaluativa/frameworks/api/schemas.py` | `CrearSesionEnVivoRequest`/`SesionEnVivoResponse` |
| `src/actividad_evaluativa/frameworks/dependencies.py` | Wiring de `CrearSesionEnVivoUseCase`/`SesionesEnVivoController` |
| `tests/unit/inc6/test_crear_sesion_en_vivo.py` | Tests unitarios del Use Case con Fakes |
| `tests/integration/inc6/test_sesiones_en_vivo_router.py` | Tests HTTP del endpoint |
| `tests/features/inc6/US-6.1.2.feature` + step defs | BDD de los criterios de aceptación de arriba |

---

## Referencias

- Modelo de dominio: `docs/design/domain/BC-actividad-evaluativa-modelo.md` §12 (línea de
  tiempo), §13 (`CrearSesionEnVivo` → `SesionEnVivoCreada`), §14 (aggregate e invariantes)
- Precedente directo: `US-3.1.2` (`CrearActividadPeriodoAbierto`, mismo patrón de construcción
  de aggregate con set de preguntas sampleado, `docs/specs/inc3/US-3.1.2.md` si existe, o
  `docs/reports/inc3/US-3.1.2-report.md`)
- Depende de: `US-6.1.1` (`ComisionConsultaPort`)
- Consumida por: `US-6.1.3`, `US-6.1.4` y toda la Iteración 2
- Candidatas: `docs/plans/inc6/inc6-candidatas.md`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
