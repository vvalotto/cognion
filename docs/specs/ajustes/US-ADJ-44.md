# US-ADJ-44: Docente consulta el desempeño de una Comisión completa

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-5-ADJ.4`
**Tipo**: `feat backend`
**Agregado principal afectado**: — (BC sin aggregate propio, `BC-analytics-modelo.md` §2)
**Bounded Context**: Analytics (con guard ampliado en Actividad Evaluativa)

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **ver de un vistazo el % de aciertos acumulado y las actividades pendientes de cada
estudiante de una Comisión, con acceso al detalle de una evaluación puntual**
para **priorizar a quién atender sin revisar comisión por comisión ni estudiante por
estudiante (RF-20)**.

---

## Contexto del dominio

### Problema

`US-4.2.1` ya expone el desempeño de un Estudiante elegido; falta la vista agregada por
Comisión completa, con dos niveles de drill-down: detalle de un estudiante (reusa `US-4.2.1`
sin cambios) y de ahí a la revisión completa de una evaluación puntual (`GET
/evaluaciones/{id}/revision`, `US-3.2.3`, hoy exclusiva del Estudiante dueño). Ninguna query
existente calcula "actividades pendientes" — hace falta saber qué actividades de la materia
están abiertas *ahora* y visibles para la comisión, lo que obliga a leer
`ActividadEvaluativaPeriodoAbierto` (BC Actividad Evaluativa) desde Analytics por primera vez.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Port (extendido) | `EvaluacionDesempenoConsultaPort.listar_actividades_abiertas(materia_id, comision_id)` | `list[UUID]` de `actividad_id` con `fecha_apertura ≤ ahora ≤ fecha_cierre`, `cerrada_manualmente = false`, visibles a `comision_id` (`comisiones_ids` vacío = todas) |
| Use Case (nuevo) | `ObtenerDesempenoPorComisionUseCase` | Compone `ComisionConsultaPort.listar_estudiantes` (roster) + `EvaluacionDesempenoConsultaPort.listar_evaluaciones_finalizadas` (por estudiante) + `listar_actividades_abiertas`; arma una fila por estudiante |
| Controller (extendido) | `AnalyticsController` | Método nuevo `obtener_desempeno_por_comision(materia_id, comision_id)` |
| Endpoint (nuevo) | `GET /analytics/materias/{materia_id}/comisiones/{comision_id}/desempeno` | Rol `docente` |
| Use Case (modificado, BC Actividad Evaluativa) | `ObtenerRevisionEvaluacionUseCase` | Admite un llamador Docente además del Estudiante dueño — ver §"Drill-down 2° nivel" |
| Endpoint (modificado, BC Actividad Evaluativa) | `GET /evaluaciones/{evaluacion_id}/revision` | Guard ampliado: `require_estudiante` → acepta también `require_docente` |

---

## Especificacion del comportamiento

### Precondicion

- `US-4.2.2` (`ComisionConsultaPort`), `US-4.1.1` (`EvaluacionDesempenoConsultaPort`) implementadas.
- Docente autenticado (JWT válido, rol `docente`).
- `materia_id` y `comision_id` existen; `comision_id` pertenece a `materia_id`.

### Postcondicion

- 200 con una fila por estudiante de la comisión: `estudiante_id`, `nombre`,
  `porcentaje_aciertos_acumulado: float | None` (`None` = "Sin datos" — estudiante sin ninguna
  `Evaluacion` finalizada en la materia, **nunca `0%`** — a diferencia de
  `ResumenDesempeno.porcentaje_acierto` de `US-4.1.2`, que sí devuelve `0` sin datos; acá se
  distingue explícitamente), `actividades_pendientes: int` (actividades de
  `listar_actividades_abiertas(materia_id, comision_id)` sin `Evaluacion` `Finalizada` de ese
  estudiante — no distingue sin-iniciar de en-curso/suspendida, ese detalle es RF-23/`US-ADJ-47`).
- Comisión sin ningún estudiante con evaluaciones finalizadas: la tabla se arma igual, todos en
  "Sin datos" (`porcentaje_aciertos_acumulado = null`), `actividades_pendientes` calculado
  igual sobre las actividades abiertas vigentes.
- `comision_id` que no pertenece a `materia_id` → 422 (`ComisionNoPerteneceAMateria`, reusa la
  excepción de `US-4.2.4`).
- Sin JWT válido → 401. Rol distinto de `docente` → 403.
- **Drill-down 2° nivel** (`GET /evaluaciones/{id}/revision`, guard ampliado): un Docente
  autenticado puede pedir la revisión de una `Evaluacion` de cualquier Estudiante — **sin
  restricción de pertenencia a una comisión que ese Docente dicte**, mismo precedente de RBAC
  estándar por rol ya resuelto con Víctor para `US-4.2.1` (`analytics_router.py`, comentario de
  `obtener_desempeno_de_estudiante`: "sin restricción de pertenencia... RBAC estándar de rol
  docente"). El modelo de dominio (`BC-analytics-modelo.md` §8.4, hot spot 3) proponía
  restringir a "Docente de la materia", pero el dominio actual no modela pertenencia
  Docente↔Materia en ningún punto del sistema (`Comision.docentes_asignados` liga Docente↔
  Comisión, no Materia) — extenderlo solo para esta US sería alcance nuevo no pedido. Se aplica
  el mismo criterio ya vigente en todo Analytics. Queda anotado para la revisión documental de
  cierre (`US-ADJ-52`) si Víctor decide ajustar el modelo.
- `Evaluacion` no `Finalizada` (Docente pide revisión de una que sigue en curso) → mismo error
  que hoy, `EvaluacionNoFinalizada` (422) — sin cambio de comportamiento, solo de quién puede
  pedirla.

### Invariantes

| ID | Invariante |
|----|------------|
| — | `porcentaje_aciertos_acumulado` es `None` sin ninguna `Evaluacion` finalizada del estudiante en la materia — nunca `0.0`. |
| — | `actividades_pendientes` solo cuenta actividades **abiertas ahora** (`fecha_apertura ≤ ahora ≤ fecha_cierre`, no cerrada manualmente) — una actividad ya vencida o cerrada no genera pendiente eterno. |

---

## Criterios de aceptacion

```gherkin
Feature: Desempeño por comisión (US-ADJ-44)

  Scenario: Comisión con estudiantes en distinto estado
    Given una comisión con un estudiante con 2 Evaluacion finalizadas y otro sin ninguna
    And una actividad abierta ahora, visible a la comisión, que el segundo estudiante no rindió
    When un Docente hace GET /analytics/materias/X/comisiones/C1/desempeno
    Then recibe 200 con el primero mostrando su % acumulado y 0 pendientes
    And el segundo con "Sin datos" (null) y 1 actividad pendiente

  Scenario: Comisión sin ninguna evaluación finalizada
    Given una comisión cuyos estudiantes nunca finalizaron ninguna Evaluacion
    When un Docente consulta su desempeño
    Then recibe 200 con todos los estudiantes en "Sin datos"

  Scenario: Comisión que no pertenece a la materia
    Given una comisión de otra materia
    When un Docente hace GET /analytics/materias/X/comisiones/{esa comisión}/desempeno
    Then recibe 422

  Scenario: Drill-down a revisión de una evaluación ajena
    Given una Evaluacion Finalizada de un Estudiante que no es el que hace la request
    When un Docente hace GET /evaluaciones/{id}/revision
    Then recibe 200 con el detalle completo, igual que si la pidiera el propio Estudiante

  Scenario: Rol distinto de Docente
    Given un Estudiante autenticado
    When hace GET /analytics/materias/X/comisiones/C1/desempeno
    Then recibe 403
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] Sí — primera vez que Analytics lee `ActividadEvaluativaPeriodoAbierto` (no solo el
  stream de `Evaluacion`) a través de `EvaluacionDesempenoConsultaPort`, ya anticipado y
  aprobado en `BC-analytics-modelo.md` §8.2/§8.3 (`US-ADJ-33`) — no es una decisión nueva de
  esta US, solo su primera implementación concreta.

**Capa(s) afectadas:**
- [ ] Entities — sin cambios
- [x] Use Cases — `ObtenerDesempenoPorComisionUseCase` (nuevo, BC Analytics);
  `ObtenerRevisionEvaluacionUseCase` (modificado, BC Actividad Evaluativa: acepta llamador
  Docente sin exigir `estudiante_id` de dueño)
- [x] Interface Adapters — `AnalyticsController` (método nuevo); `RevisionController` (guard
  de rol, no de lógica)
- [x] Frameworks — `EvaluacionDesempenoConsultaPort` gana `listar_actividades_abiertas`
  (adapter ampliado); `analytics_router.py` agrega el `GET`; `revision_router.py` amplía la
  dependencia de rol
- [ ] Frontend — no aplica a esta US (`US-ADJ-48`)

---

## Fuente de verdad UX

No aplica a esta US — endpoints backend puros. La pantalla que los consume
(`#doc-desempeno-comision`, con sus dos niveles de drill-down) se especifica en `US-ADJ-48`
contra `docs/design/ux/wireframes-analytics.md` §3.2.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/analytics/entities/ports/evaluacion_desempeno_consulta_port.py` | Agrega `listar_actividades_abiertas(materia_id, comision_id) -> list[UUID]` |
| `src/analytics/frameworks/adapters/evaluacion_desempeno_consulta_port_in_process.py` | Implementa el método nuevo leyendo streams `ActividadEvaluativaPeriodoAbierto` |
| `src/analytics/use_cases/obtener_desempeno_por_comision.py` | Nuevo — `ObtenerDesempenoPorComisionUseCase` |
| `src/analytics/interface_adapters/controllers/analytics_controller.py` | Método nuevo |
| `src/analytics/frameworks/api/analytics_router.py` | Agrega `GET /materias/{materia_id}/comisiones/{comision_id}/desempeno` |
| `src/actividad_evaluativa/use_cases/obtener_revision_evaluacion.py` | Admite llamador Docente (sin exigir `evaluacion.estudiante_id == estudiante_id`) |
| `src/actividad_evaluativa/frameworks/api/revision_router.py` | Guard ampliado a `require_estudiante` **o** `require_docente` |
| `tests/unit/inc5-adj/` y `tests/integration/inc5-adj/` | Tests del Use Case y de ambos endpoints (mix de estados, sin datos, 422, drill-down docente, 403) |

---

## Referencias

- Modelo de dominio: `docs/design/domain/BC-analytics-modelo.md` §8.2/§8.3/§8.4 (hot spot 3)
- Wireframes: `docs/design/ux/wireframes-analytics.md` §3.2
- Depende de: `US-4.1.1` (#232), `US-4.2.2` (#241)
- Consumida por: `US-ADJ-48`
- Candidatas: `docs/plans/inc5-adj/inc5-adj-candidatas.md` §Iteración 4
- Issue: [#354](https://github.com/vvalotto/cognion/issues/354)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
