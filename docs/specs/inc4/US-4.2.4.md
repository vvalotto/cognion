# US-4.2.4: Docente consulta la tasa de error por unidad/tema de una materia

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-4.2`
**Tipo**: `feat backend`
**Agregado principal afectado**: — (BC sin aggregate propio, `BC-analytics-modelo.md` §2)
**Bounded Context**: Analytics

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **ver qué unidades/temas concentran más errores en una materia, para toda la materia o
acotado a una comisión**
para **decidir dónde reforzar la enseñanza sin revisar evaluación por evaluación (RF-17)**.

---

## Contexto del dominio

### Problema

Ninguna de las dos queries de la Iteración 1 agrega por tema — hace falta un segundo método en
`EvaluacionDesempenoConsultaPort` que devuelva respuestas individuales (no solo el resumen por
evaluación), y combinarlas con el metadato de cada pregunta (`US-4.2.3`) y, opcionalmente, el
roster de una comisión (`US-4.2.2`) para acotar el agregado (`BC-analytics-modelo.md` §4/§6).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Port (extendido) | `EvaluacionDesempenoConsultaPort.listar_respuestas_vigentes_de_materia(materia_id, estudiante_ids: list[UUID] \| None)` | Una fila por `Respuesta` vigente (`pregunta_id`, `estudiante_id`, `es_correcta`) de toda `Evaluacion` finalizada de la materia, filtrado a `estudiante_ids` si se indica |
| Use Case (nuevo) | `ObtenerTasaErrorPorTemaUseCase` | Compone `listar_respuestas_vigentes_de_materia` (con el roster de `ComisionConsultaPort.listar_estudiantes` si `comision_id` viene informado) + `PreguntaMetadatoConsultaPort.obtener_metadatos`, agrupa por `(unidad_tematica, tema)` y calcula `cantidad_respuestas`, `cantidad_incorrectas`, `tasa_error` |
| Controller (extendido) | `AnalyticsController` | Nuevo método `obtener_tasa_error_por_tema(materia_id, comision_id?)` |
| Endpoint (nuevo) | `GET /analytics/materias/{materia_id}/tasa-error-por-tema?comision_id=` | Rol `docente` |

---

## Especificacion del comportamiento

### Precondicion

- `US-4.2.2` y `US-4.2.3` implementadas.
- Docente autenticado (JWT válido, rol `docente`).
- `materia_id` existe. `comision_id`, si se indica, pertenece a `materia_id`.

### Postcondicion

- Materia con `Evaluacion` finalizadas → 200 con lista de `{unidad_tematica, tema,
  cantidad_respuestas, cantidad_incorrectas, tasa_error}`, ordenada por `tasa_error`
  descendente (temas más problemáticos primero).
- `comision_id` informado → el agregado se acota a las respuestas de los estudiantes de esa
  comisión (`ComisionConsultaPort.listar_estudiantes`); omitido → agrega todas las comisiones
  de la materia.
- Materia (o comisión) sin ninguna `Evaluacion` finalizada → 200 con lista vacía.
- Respuestas de preguntas sin metadato resoluble (`US-4.2.3`, id no encontrado) → excluidas del
  agregado, sin romper el cálculo del resto.
- `comision_id` que no pertenece a `materia_id` → 422.
- Sin JWT válido → 401. Rol distinto de `docente` → 403.

### Invariantes

| ID | Invariante |
|----|------------|
| — | `tasa_error = cantidad_incorrectas / cantidad_respuestas`, nunca divide por cero — un `(unidad_tematica, tema)` sin ninguna respuesta no aparece en el resultado. |
| — | El agregado usa la `Respuesta` vigente por `pregunta_id` de cada `Evaluacion` (no cuenta reintentos ya sobrescritos), mismo criterio que `respuesta_vigente_de` de Actividad Evaluativa. |

---

## Criterios de aceptacion

```gherkin
Feature: Tasa de error por tema de una materia (US-4.2.4)

  Scenario: Materia completa, sin filtrar por comisión
    Given una materia con Evaluacion finalizadas de 2 comisiones distintas
    When un Docente hace GET /analytics/materias/X/tasa-error-por-tema
    Then recibe 200 con la tasa de error agregada de ambas comisiones, ordenada descendente

  Scenario: Acotado a una comisión
    Given la misma materia de arriba
    When un Docente hace GET /analytics/materias/X/tasa-error-por-tema?comision_id=C1
    Then recibe 200 con la tasa de error calculada solo sobre los estudiantes de C1

  Scenario: Materia sin evaluaciones finalizadas
    Given una materia sin ninguna Evaluacion finalizada
    When un Docente hace GET /analytics/materias/Y/tasa-error-por-tema
    Then recibe 200 con lista vacía

  Scenario: Comisión que no pertenece a la materia
    Given una comisión de otra materia
    When un Docente hace GET /analytics/materias/X/tasa-error-por-tema?comision_id={esa comisión}
    Then recibe 422

  Scenario: Rol distinto de Docente
    Given un Estudiante autenticado
    When hace GET /analytics/materias/X/tasa-error-por-tema
    Then recibe 403
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — compone puertos ya definidos en `US-4.2.2`/`US-4.2.3` y extiende
  `EvaluacionDesempenoConsultaPort` con un segundo método, mismo patrón de agregación en
  memoria ya usado en `US-4.1.2`.

**Capa(s) afectadas:**
- [ ] Entities — sin cambios
- [x] Use Cases — `ObtenerTasaErrorPorTemaUseCase` (nuevo)
- [x] Interface Adapters — `AnalyticsController` (método nuevo)
- [x] Frameworks — `EvaluacionDesempenoConsultaPort` gana `listar_respuestas_vigentes_de_materia`
  (adapter existente de `US-4.1.1`, extendido); `analytics_router.py` agrega el `GET`
- [ ] Frontend — no aplica a esta US (`US-4.2.6`)

---

## Fuente de verdad UX

No aplica a esta US — endpoint backend puro. La pantalla que lo consume
(`#doc-desempeno-tema`) se especifica en `US-4.2.6` contra
`docs/design/ux/wireframes-analytics.md` §3.1 (umbrales de color ≥50%/20-49%/<20%, a
implementar del lado del frontend, no en este endpoint).

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/analytics/entities/ports/evaluacion_desempeno_consulta_port.py` | Agrega `listar_respuestas_vigentes_de_materia` |
| `src/analytics/frameworks/adapters/evaluacion_desempeno_consulta_port_in_process.py` | Implementa el método nuevo |
| `src/analytics/use_cases/obtener_tasa_error_por_tema.py` | Nuevo — `ObtenerTasaErrorPorTemaUseCase` |
| `src/analytics/interface_adapters/controllers/analytics_controller.py` | Método nuevo |
| `src/analytics/frameworks/api/analytics_router.py` | Agrega `GET /materias/{materia_id}/tasa-error-por-tema` |
| `tests/unit/inc4/` y `tests/integration/inc4/` | Tests del Use Case y del endpoint (agregado total, por comisión, vacío, 422, 403) |

---

## Referencias

- Modelo de dominio: `docs/design/domain/BC-analytics-modelo.md` §4/§6 (hot spot 2)
- Depende de: `US-4.2.2` (#241), `US-4.2.3` (#242)
- Consumida por: `US-4.2.6`
- Candidatas: `docs/plans/inc4/inc4-candidatas.md` §Iteración 2
- Issue: #243

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
