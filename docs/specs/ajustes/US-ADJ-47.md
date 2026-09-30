# US-ADJ-47: Docente consulta la completitud de una actividad puntual

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-5-ADJ.4`
**Tipo**: `feat backend`
**Agregado principal afectado**: — (BC sin aggregate propio, `BC-analytics-modelo.md` §2)
**Bounded Context**: Analytics

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **ver, para una actividad puntual, el estado de cada estudiante del roster aplicable
(sin iniciar, en curso, suspendida o finalizada)**
para **saber quién todavía no rindió antes de que cierre el período, sin revisar estudiante por
estudiante (RF-23)**.

---

## Contexto del dominio

### Problema

Ninguna query existente distingue estados intermedios de `Evaluacion` (`en_curso`,
`suspendida`) — `listar_evaluaciones_finalizadas` (`US-4.1.1`) solo ve las que llegaron a
`Finalizada`. Hace falta leer el stream de `Evaluacion` sin exigir ese estado final, y resolver
el roster aplicable: la(s) comisión(es) a la(s) que la actividad está restringida
(`comisiones_ids`), o toda la materia si no hay restricción — decisión ya tomada con Víctor
(`BC-analytics-modelo.md` §8.4, hot spot 4).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Port (extendido) | `EvaluacionDesempenoConsultaPort.obtener_actividad_resumen(actividad_id)` | `ActividadResumen(materia_id, comisiones_ids) \| None` — resuelve a qué materia pertenece la actividad y a qué comisiones está restringida (vacío = todas), para poder armar el roster |
| Port (extendido) | `EvaluacionDesempenoConsultaPort.listar_estados_de_actividad(actividad_id, estudiante_ids)` | `dict[UUID, EstadoEvaluacion]` — estado (`en_curso`, `suspendida` o `finalizada`) de la `Evaluacion` de cada estudiante del roster para esa actividad puntual; un `estudiante_id` ausente del dict nunca inició |
| Use Case (nuevo) | `ObtenerCompletitudPorActividadUseCase` | Resuelve el roster (comisión(es) restringida(s) o toda la materia vía `ComisionConsultaPort`), llama `listar_estados_de_actividad`, completa con `sin_iniciar` los ausentes |
| Controller (extendido) | `AnalyticsController` | Método nuevo `obtener_completitud_por_actividad(actividad_id)` |
| Endpoint (nuevo) | `GET /analytics/actividades/{actividad_id}/completitud` | Rol `docente` |

---

## Especificacion del comportamiento

### Precondicion

- `US-4.2.2` implementada. `US-ADJ-44` recomendada antes (primer método que lee
  `ActividadEvaluativaPeriodoAbierto` desde Analytics; este reusa el mismo cruce).
- Docente autenticado.
- `actividad_id` existe.

### Postcondicion

- 200 con `resumen` (4 números: `finalizadas`, `en_curso`, `suspendidas`, `sin_iniciar`) y
  `detalle`: una fila por estudiante del roster aplicable — `estudiante_id`, `nombre`,
  `comision_id`, `estado` ∈ `{sin_iniciar, en_curso, suspendida, finalizada}`.
- `comisiones_ids` de la actividad no vacío → roster = unión de los estudiantes de esas
  comisiones puntuales (vía `ComisionConsultaPort.listar_estudiantes` por cada una, sin
  duplicar si un estudiante estuviera en más de una — caso hoy imposible por el modelo actual
  de una comisión por estudiante, pero el Use Case no asume unicidad de origen).
- `comisiones_ids` vacío → roster = unión de **todas** las comisiones de la materia
  (`ComisionConsultaPort.listar_comisiones_por_materia` + `listar_estudiantes` de cada una).
- `actividad_id` inexistente → 404.
- Sin JWT válido → 401. Rol distinto de `docente` → 403.

### Invariantes

| ID | Invariante |
|----|------------|
| — | Todo estudiante del roster aplicable aparece exactamente una vez en `detalle`, sin excepción — un estudiante que nunca inició `Evaluacion` no queda ausente del reporte, se completa como `sin_iniciar`. |
| — | `resumen` es siempre la suma de los 4 conteos del `detalle` — invariante de consistencia interna, no de dominio (se verifica en el test, no en runtime). |

---

## Criterios de aceptacion

```gherkin
Feature: Completitud por actividad (US-ADJ-47)

  Scenario: Actividad restringida a una comisión, estados mixtos
    Given una actividad restringida a la comisión C1 con 4 estudiantes
    And 1 finalizó, 1 está en curso, 1 suspendió y 1 nunca inició
    When un Docente hace GET /analytics/actividades/X/completitud
    Then recibe 200 con resumen {finalizadas: 1, en_curso: 1, suspendidas: 1, sin_iniciar: 1}
    And el detalle lista los 4 estudiantes con su estado exacto

  Scenario: Actividad sin restricción de comisión
    Given una actividad sin comisiones_ids (visible a toda la materia, 2 comisiones)
    When un Docente consulta su completitud
    Then el roster del detalle incluye los estudiantes de ambas comisiones

  Scenario: Actividad inexistente
    Given un actividad_id que no corresponde a ninguna actividad
    When un Docente consulta su completitud
    Then recibe 404

  Scenario: Rol distinto de Docente
    Given un Estudiante autenticado
    When hace GET /analytics/actividades/X/completitud
    Then recibe 403
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — extiende el mismo cruce hacia `ActividadEvaluativaPeriodoAbierto` ya introducido en
  `US-ADJ-44`, sin puerto nuevo.

**Capa(s) afectadas:**
- [ ] Entities — sin cambios
- [x] Use Cases — `ObtenerCompletitudPorActividadUseCase` (nuevo)
- [x] Interface Adapters — `AnalyticsController` (método nuevo)
- [x] Frameworks — `EvaluacionDesempenoConsultaPort` gana `obtener_actividad_resumen` y
  `listar_estados_de_actividad` (adapter ampliado); `analytics_router.py` agrega el `GET`
- [ ] Frontend — no aplica a esta US (`US-ADJ-51`)

---

## Fuente de verdad UX

No aplica a esta US — endpoint backend puro. La pantalla que lo consume
(`#doc-completitud-actividad`) se especifica en `US-ADJ-51` contra
`docs/design/ux/wireframes-analytics.md` §3.5.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/analytics/entities/ports/evaluacion_desempeno_consulta_port.py` | Agrega `obtener_actividad_resumen(actividad_id)` y `listar_estados_de_actividad(actividad_id, estudiante_ids)` |
| `src/analytics/frameworks/adapters/evaluacion_desempeno_consulta_port_in_process.py` | Implementa ambos métodos nuevos |
| `src/analytics/use_cases/obtener_completitud_por_actividad.py` | Nuevo |
| `src/analytics/interface_adapters/controllers/analytics_controller.py` | Método nuevo |
| `src/analytics/frameworks/api/analytics_router.py` | Agrega `GET /actividades/{actividad_id}/completitud` |
| `tests/unit/inc5-adj/` y `tests/integration/inc5-adj/` | Tests del Use Case y del endpoint (mix de estados, sin restricción de comisión, 404, 403) |

---

## Referencias

- Modelo de dominio: `docs/design/domain/BC-analytics-modelo.md` §8.2/§8.3/§8.4 (hot spot 4)
- Wireframes: `docs/design/ux/wireframes-analytics.md` §3.5
- Depende de: `US-4.2.2` (#241), `US-ADJ-44`
- Consumida por: `US-ADJ-51`
- Candidatas: `docs/plans/inc5-adj/inc5-adj-candidatas.md` §Iteración 4
- Issue: [#357](https://github.com/vvalotto/cognion/issues/357)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
