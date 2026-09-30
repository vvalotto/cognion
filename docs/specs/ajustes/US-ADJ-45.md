# US-ADJ-45: Docente consulta la evolución temporal de aciertos

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-5-ADJ.4`
**Tipo**: `feat backend`
**Agregado principal afectado**: — (BC sin aggregate propio, `BC-analytics-modelo.md` §2)
**Bounded Context**: Analytics

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **ver cómo evolucionó el % de aciertos de un estudiante puntual, comparado contra el
promedio de su comisión, actividad tras actividad**
para **detectar si un estudiante viene mejorando o empeorando, no solo su promedio acumulado
(RF-21)**.

---

## Contexto del dominio

### Problema

Las queries existentes (`US-4.1.2`, `US-ADJ-44`) devuelven un acumulado o un listado sin orden
cronológico explícito de series comparadas. Hace falta una vista temporal, tanto individual
como de comisión, ordenada por actividad efectivamente rendida — sin depender de la fecha de
apertura de la actividad, que el DTO existente no expone (`BC-analytics-modelo.md` §8.4, hot
spot 2: se usa `min(finalizada_en)` del grupo como proxy).

**Gap detectado en esta spec (no cubierto por `BC-analytics-modelo.md` §8.3):** el wireframe
(`wireframes-analytics.md` §3.3) etiqueta el eje X "por título de actividad", pero
`EvaluacionDesempenoResumen` (`US-4.1.1`) no trae `titulo` de la actividad — solo
`actividad_id`. Se resuelve agregando un método de resolución de título por lote al mismo
puerto que ya cruza hacia Actividad Evaluativa (`listar_actividades_abiertas`, `US-ADJ-44`),
mismo criterio de "el puerto crece, no se crea uno nuevo por RF" (§8.2).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Port (extendido) | `EvaluacionDesempenoConsultaPort.obtener_titulos_actividades(actividad_ids)` | `dict[UUID, str]` — título de cada actividad, para el eje X del gráfico (gap detectado arriba) |
| Use Case (nuevo) | `ObtenerEvolucionTemporalEstudianteUseCase` | Compone `listar_evaluaciones_finalizadas(estudiante_id, materia_id)` (`US-4.1.1`, ya existente) ordenado por `finalizada_en` ascendente + `obtener_titulos_actividades` |
| Use Case (nuevo) | `ObtenerEvolucionTemporalComisionUseCase` | Compone `ComisionConsultaPort.listar_estudiantes` (roster) + `listar_evaluaciones_finalizadas` por estudiante, agrupa por `actividad_id`, promedia `porcentaje_acierto` entre quienes finalizaron esa actividad, ordena por `min(finalizada_en)` del grupo + `obtener_titulos_actividades` |
| Controller (extendido) | `AnalyticsController` | Métodos nuevos `obtener_evolucion_temporal_estudiante(materia_id, estudiante_id)` y `obtener_evolucion_temporal_comision(materia_id, comision_id)` |
| Endpoint (nuevo) | `GET /analytics/materias/{materia_id}/estudiantes/{estudiante_id}/evolucion-temporal` | Rol `docente` |
| Endpoint (nuevo) | `GET /analytics/materias/{materia_id}/comisiones/{comision_id}/evolucion-temporal` | Rol `docente` |

---

## Especificacion del comportamiento

### Precondicion

- `US-4.1.1`, `US-4.2.2` implementadas. `US-ADJ-44` recomendada antes (mismo puerto que crece).
- Docente autenticado.
- `materia_id`, `estudiante_id`/`comision_id` existen y son coherentes entre sí (`comision_id`
  pertenece a `materia_id`, igual criterio de 422 que `US-4.2.4`/`US-ADJ-44`).

### Postcondicion

- **Individual**: 200 con una fila por `Evaluacion` finalizada del estudiante en la materia,
  ordenada por `finalizada_en` ascendente: `actividad_id`, `titulo_actividad`,
  `finalizada_en`, `porcentaje_acierto` (por evaluación, `cantidad_correctas /
  (cantidad_correctas + cantidad_incorrectas)`, redondeado igual que `ResumenDesempeno`).
- **Comisión**: 200 con una fila por `actividad_id` con al menos una `Evaluacion` finalizada de
  algún estudiante del roster: `actividad_id`, `titulo_actividad`,
  `porcentaje_aciertos_promedio` (promedio simple entre quienes finalizaron esa actividad —
  quien no la rindió no entra al promedio, **no cuenta como 0%**), ordenada por
  `min(finalizada_en)` del grupo.
- Estudiante/comisión sin ninguna `Evaluacion` finalizada → 200 con lista vacía (el frontend
  decide cómo mostrar 0 o 1 punto, `US-ADJ-49`).
- `comision_id`/`estudiante_id` inexistente o que no pertenece a `materia_id` → 422/404 según
  corresponda (mismo criterio que endpoints hermanos: `estudiante_id` inexistente → 404, igual
  que `obtener_desempeno_de_estudiante`, `US-4.2.1`; `comision_id` que no pertenece a la
  materia → 422, `ComisionNoPerteneceAMateria`).
- Sin JWT válido → 401. Rol distinto de `docente` → 403.

### Invariantes

| ID | Invariante |
|----|------------|
| — | El orden cronológico se basa siempre en `finalizada_en` real (individual) o `min(finalizada_en)` del grupo (comisión) — nunca en la fecha de apertura de la actividad, que puede no coincidir con cuándo efectivamente se rindió. |
| — | Una actividad sin ninguna `Evaluacion` finalizada de nadie del roster simplemente no aparece en la serie de comisión — nunca un punto en 0%. |

---

## Criterios de aceptacion

```gherkin
Feature: Evolución temporal de aciertos (US-ADJ-45)

  Scenario: Serie individual con 3 evaluaciones
    Given un estudiante con 3 Evaluacion finalizadas en distintas fechas y % de acierto
    When un Docente hace GET .../estudiantes/{id}/evolucion-temporal
    Then recibe 200 con 3 puntos ordenados cronológicamente, cada uno con el título de su actividad

  Scenario: Serie de comisión con participación parcial
    Given una comisión de 3 estudiantes donde solo 2 finalizaron la actividad A
    When un Docente hace GET .../comisiones/{id}/evolucion-temporal
    Then el punto de la actividad A promedia solo esos 2 estudiantes, no los 3

  Scenario: Estudiante sin evaluaciones finalizadas
    Given un estudiante sin ninguna Evaluacion finalizada en la materia
    When un Docente consulta su evolución
    Then recibe 200 con lista vacía

  Scenario: Comisión que no pertenece a la materia
    Given una comisión de otra materia
    When un Docente hace GET /analytics/materias/X/comisiones/{esa comisión}/evolucion-temporal
    Then recibe 422

  Scenario: Rol distinto de Docente
    Given un Estudiante autenticado
    When hace GET .../evolucion-temporal
    Then recibe 403
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — extiende un puerto ya ampliado en `US-ADJ-44`, mismo patrón de agregación en
  memoria de toda la Iteración 4.

**Capa(s) afectadas:**
- [ ] Entities — sin cambios
- [x] Use Cases — `ObtenerEvolucionTemporalEstudianteUseCase`,
  `ObtenerEvolucionTemporalComisionUseCase` (nuevos)
- [x] Interface Adapters — `AnalyticsController` (2 métodos nuevos)
- [x] Frameworks — `EvaluacionDesempenoConsultaPort` gana `obtener_titulos_actividades`
  (adapter ampliado); `analytics_router.py` agrega los 2 `GET`
- [ ] Frontend — no aplica a esta US (`US-ADJ-49`)

---

## Fuente de verdad UX

No aplica a esta US — endpoints backend puros. La pantalla que los consume
(`#doc-evolucion-temporal`, gráfico de línea con 2 series) se especifica en `US-ADJ-49` contra
`docs/design/ux/wireframes-analytics.md` §3.3.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/analytics/entities/ports/evaluacion_desempeno_consulta_port.py` | Agrega `obtener_titulos_actividades(actividad_ids) -> dict[UUID, str]` |
| `src/analytics/frameworks/adapters/evaluacion_desempeno_consulta_port_in_process.py` | Implementa el método nuevo |
| `src/analytics/use_cases/obtener_evolucion_temporal_estudiante.py` | Nuevo |
| `src/analytics/use_cases/obtener_evolucion_temporal_comision.py` | Nuevo |
| `src/analytics/interface_adapters/controllers/analytics_controller.py` | 2 métodos nuevos |
| `src/analytics/frameworks/api/analytics_router.py` | Agrega los 2 `GET` |
| `tests/unit/inc5-adj/` y `tests/integration/inc5-adj/` | Tests de ambos Use Case y endpoints (serie completa, participación parcial, vacío, 422, 404, 403) |

---

## Referencias

- Modelo de dominio: `docs/design/domain/BC-analytics-modelo.md` §8.3 (hot spot 2)
- Wireframes: `docs/design/ux/wireframes-analytics.md` §3.3
- Depende de: `US-4.1.1` (#232), `US-4.2.2` (#241), `US-ADJ-44`
- Consumida por: `US-ADJ-49`
- Candidatas: `docs/plans/inc5-adj/inc5-adj-candidatas.md` §Iteración 4
- Issue: [#355](https://github.com/vvalotto/cognion/issues/355)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
