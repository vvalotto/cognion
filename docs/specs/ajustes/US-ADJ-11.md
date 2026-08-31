# US-ADJ-11: Fix — IniciarEvaluacion no rechaza actividad cerrada manualmente

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-3.4` (ajuste inmediato, corregido en la misma sesión de UAT —
no forma parte de un `SP-ADJ` diferido)
**Tipo**: `fix backend`
**Agregado principal afectado**: `IniciarEvaluacionUseCase` (sin cambios de invariantes de
dominio — `ActividadEvaluativaPeriodoAbierto.cerrada_manualmente` ya existe desde `US-3.3.2`)
**Bounded Context**: Actividad Evaluativa
**Origen**: hallazgos de UAT de cierre de la Iteración 4, 2026-08-31. Issue
[#192](https://github.com/vvalotto/cognion/issues/192) (1er hallazgo, PR
[#193](https://github.com/vvalotto/cognion/pull/193), ya mergeado).
**ID anterior**: `US-3.4.10` — renombrado a la convención `US-ADJ` el 2026-08-31 (decisión de
Víctor: los hallazgos de UAT corregidos como US-IEDD aparte, diferidos o no, se numeran como
ajuste). Los commits/PRs históricos (#192, #193, #194) referencian el ID anterior — no se
reescribió el historial de git.

## Alcance 2 — carrera real al iniciar evaluación (detectado en el recorrido manual, mismo día)

El recorrido en navegador real (`design-iter4.md`) detectó un segundo bug, distinto del
anterior pero en el mismo Use Case: `IniciarEvaluacionUseCase` no protegía la creación del
primer evento contra una escritura concurrente genuina — dos `POST /evaluaciones` simultáneos
del mismo Estudiante (reproducible con React StrictMode en desarrollo, o un doble clic real en
producción) causaban que uno de los dos requests recibiera `500 Internal Server Error`
(`IntegrityError` de Postgres sin traducir, violación de `uq_events_stream_sequence`) en vez de
la misma `Evaluacion` que el otro — rompiendo la promesa de idempotencia de INV-AE-05/06 ante
una carrera real, no solo secuencial.

**Fix:** `SQLAlchemyEventStore.append()` traduce la violación real del índice único
(`IntegrityError` al `commit`) en `ConcurrenciaOptimistaError` — el índice ya existía como
respaldo documentado en su propio docstring, pero nunca se traducía. `IniciarEvaluacionUseCase`
captura esa excepción al insertar el primer evento y relee el stream para devolver la
`Evaluacion` que ganó la carrera, en vez de propagar el error.

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **que cerrar una actividad manualmente bloquee también a los estudiantes que todavía no
habían empezado a rendirla**
para **que el cierre manual (`US-3.3.2`) termine realmente la actividad, no solo a quienes ya
estaban respondiendo**.

---

## Contexto del dominio

### Problema

`IniciarEvaluacionUseCase.execute()` solo valida la ventana de fechas:

```python
ahora = datetime.now(UTC)
if ahora < fecha_apertura or ahora > fecha_cierre:
    raise FueraDePeriodo(actividad_id, ahora)
```

Nunca chequea `actividad.cerrada_manualmente` — a pesar de que el docstring de la propia
excepción ya documenta el contrato completo:

> `FueraDePeriodo`: "`ahora` no está dentro de la ventana vigente de la actividad, **o está
> cerrada manualmente**."

**Consecuencia real, reproducida contra el backend vivo** (`smoke.sh`, sección "Flujo de
responder/pausar/reanudar/finalizar/revisión"): un Docente cierra una actividad manualmente
(`POST /actividades/{id}/cerrar`, `US-3.3.2`) antes de su `fecha_cierre` natural — exactamente
el caso de uso de esa US ("terminar con estudiantes todavía respondiendo"). `ahora` sigue
dentro de `[fecha_apertura, fecha_cierre]`, así que un Estudiante que **todavía no había
iniciado** su evaluación puede arrancar una nueva sin ningún rechazo (`POST /evaluaciones`
devuelve `200`, no `422`). El cierre manual solo finaliza en cascada las `Evaluacion`
`EnCurso` existentes (`CerrarActividadUseCase`, Regla 3 del `VerificadorDeVencimientos`) — no
impide nuevos inicios.

Ningún test automatizado lo agarró porque ninguno de los escenarios de `US-3.1.3`/`US-3.3.2`
combina "actividad cerrada manualmente" + "estudiante nuevo, sin `Evaluacion` previa" +
"dentro de la ventana de fechas natural".

### Alcance del fix

Agregar el chequeo de `actividad.cerrada_manualmente` en `IniciarEvaluacionUseCase.execute()`,
inmediatamente junto al chequeo de ventana existente, reutilizando `FueraDePeriodo` (mismo
error que el rechazo por fecha — la UI ya lo redirige a `#est-fuera-periodo` sin distinguir
motivo, mismo criterio que `US-1.1.3`). Sin cambios de frontend, sin evento ni comando nuevo.

---

## Especificacion del comportamiento

### Precondicion

- Una `ActividadEvaluativaPeriodoAbierto` con `cerrada_manualmente = true`
  (`ActividadEvaluativaCerrada`, `US-3.3.2`), dentro de su ventana de fechas natural.

### Postcondicion

- `POST /evaluaciones` sobre esa actividad, para un Estudiante **sin** `Evaluacion` previa,
  responde `422` (`FueraDePeriodo`).
- Un Estudiante que **ya** tiene una `Evaluacion` `Finalizada` para esa actividad sigue
  entrando sin problema (`IniciarEvaluacion` idempotente devuelve la existente, `200`) — RF-13,
  la revisión sigue disponible aunque el período ya cerró. Este caso no cambia.
- El rechazo por fecha (`ahora` fuera de `[apertura, cierre]`) sigue funcionando igual.

### Invariantes

| ID | Invariante |
|----|------------|
| — | `IniciarEvaluacion` rechaza con `FueraDePeriodo` tanto si `ahora` está fuera de la ventana de fechas como si la actividad está `cerrada_manualmente = true` — mismo criterio documentado en el docstring de `FueraDePeriodo` desde `US-3.1.3`, nunca implementado hasta ahora. |

---

## Criterios de aceptacion

```gherkin
Feature: IniciarEvaluacion rechaza actividad cerrada manualmente (US-ADJ-11)

  Scenario: Estudiante nuevo intenta iniciar sobre una actividad cerrada manualmente
    Given una ActividadEvaluativaPeriodoAbierto vigente por fecha pero cerrada_manualmente = true
    And un Estudiante sin Evaluacion previa para esa actividad
    When intenta iniciar su evaluación
    Then el sistema rechaza con FueraDePeriodo (422)

  Scenario: Estudiante con Evaluacion ya Finalizada sigue accediendo (sin cambios)
    Given una ActividadEvaluativaPeriodoAbierto cerrada_manualmente = true
    And un Estudiante con una Evaluacion Finalizada para esa actividad
    When entra de nuevo (idempotente)
    Then el sistema devuelve la Evaluacion existente sin rechazar (200)
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — reutiliza `FueraDePeriodo`, ya existente, sin cambios de contrato de API.

**Capa(s) afectadas:**
- [x] Backend — `src/actividad_evaluativa/use_cases/iniciar_evaluacion.py`
- [ ] Frontend — sin cambios (el 422 ya redirige a `#est-fuera-periodo`, `US-3.4.5`)

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/actividad_evaluativa/use_cases/iniciar_evaluacion.py` | Agrega el chequeo de `actividad.cerrada_manualmente` |

---

## Referencias

- Relacionada con: `US-3.1.3` (`IniciarEvaluacion`, chequeo de ventana original), `US-3.3.2`
  (`CerrarActividad`, origen de `cerrada_manualmente`)
- Detectada durante: UAT de cierre de la Iteración 4 (`quality/reports/uat/inc3/design-iter4.md`)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
