# US-ADJ-46: Docente consulta el ranking de preguntas más falladas

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-5-ADJ.4`
**Tipo**: `feat backend`
**Agregado principal afectado**: — (BC sin aggregate propio, `BC-analytics-modelo.md` §2)
**Bounded Context**: Analytics

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **ver qué preguntas puntuales concentran más errores, ordenadas por tasa de error, para
toda la materia o acotado a una comisión**
para **revisar el enunciado de la pregunta más problemática, no solo el tema al que
pertenece (RF-22)**.

---

## Contexto del dominio

### Problema

`US-4.2.4` (RF-17) ya agrega por `(unidad_tematica, tema)`; falta el mismo agregado a nivel de
pregunta individual, con el enunciado visible. Reusa exactamente la misma fuente
(`listar_respuestas_vigentes_de_materia`) cambiando la clave de agrupación de `(unidad_tematica,
tema)` a `pregunta_id`, y necesita `enunciado` — campo que `MetadatoPreguntaResumen`
(`US-4.2.3`) todavía no expone.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| DTO (ampliado) | `MetadatoPreguntaResumen` | Agrega el campo `enunciado: str` |
| Port (sin cambio de firma) | `PreguntaMetadatoConsultaPort.obtener_metadatos` | Mismo método, el adapter ahora también trae `enunciado` |
| Use Case (nuevo) | `ObtenerRankingPreguntasFalladasUseCase` | Compone `listar_respuestas_vigentes_de_materia` (`US-4.1.1`/`US-4.2.4`, mismo `estudiante_ids` opcional por comisión) + `obtener_metadatos` (ampliado), agrupa por `pregunta_id`, calcula `cantidad_presentaciones`, `cantidad_fallos`, `tasa_error` |
| Controller (extendido) | `AnalyticsController` | Método nuevo `obtener_ranking_preguntas_falladas(materia_id, comision_id?)` |
| Endpoint (nuevo) | `GET /analytics/materias/{materia_id}/ranking-preguntas-falladas?comision_id=` | Rol `docente` |

---

## Especificacion del comportamiento

### Precondicion

- `US-4.2.2`, `US-4.2.3`, `US-4.2.4` implementadas (reusa su lógica de resolución de
  `estudiante_ids` por comisión, idéntica).
- Docente autenticado.
- `materia_id` existe. `comision_id`, si se indica, pertenece a `materia_id`.

### Postcondicion

- 200 con una fila por `pregunta_id` que apareció en al menos una `Respuesta` vigente de la
  materia (acotada a la comisión si se indica): `pregunta_id`, `enunciado`, `unidad_tematica`,
  `tema`, `cantidad_presentaciones`, `cantidad_fallos`, `tasa_error =
  cantidad_fallos / cantidad_presentaciones`, ordenada por `tasa_error` descendente (posición
  del ranking = índice en la lista, sin campo propio — el frontend numera).
- `comision_id` informado → agrega solo las respuestas de esos estudiantes; omitido → toda la
  materia (misma resolución que `US-4.2.4`).
- Materia (o comisión) sin ninguna pregunta presentada todavía → 200 con lista vacía.
- Respuestas de preguntas sin metadato resoluble (id no encontrado, mismo caso que `US-4.2.4`)
  → excluidas del agregado, sin romper el cálculo del resto.
- `comision_id` que no pertenece a `materia_id` → 422 (`ComisionNoPerteneceAMateria`, reusa la
  excepción existente).
- Sin JWT válido → 401. Rol distinto de `docente` → 403.

### Invariantes

| ID | Invariante |
|----|------------|
| — | `tasa_error = cantidad_fallos / cantidad_presentaciones`, nunca divide por cero — una pregunta sin ninguna presentación no aparece en el resultado (mismo criterio que `US-4.2.4`). |
| — | El ranking ordena por tasa de error, no por conteo bruto de fallos — una pregunta con 1 presentación y 1 fallo (100%) rankea sobre una con 50 presentaciones y 10 fallos (20%), mismo criterio explícito de la candidata (`RF-22`, "no conteo bruto"). |

---

## Criterios de aceptacion

```gherkin
Feature: Ranking de preguntas más falladas (US-ADJ-46)

  Scenario: Materia completa, sin filtrar por comisión
    Given una materia con respuestas vigentes de 5 preguntas distintas
    When un Docente hace GET /analytics/materias/X/ranking-preguntas-falladas
    Then recibe 200 con las 5 preguntas ordenadas por tasa de error descendente, con enunciado

  Scenario: Acotado a una comisión
    Given la misma materia de arriba
    When un Docente hace GET .../ranking-preguntas-falladas?comision_id=C1
    Then recibe 200 con el ranking calculado solo sobre las respuestas de C1

  Scenario: Tasa de error prevalece sobre conteo bruto
    Given una pregunta con 1 presentación y 1 fallo, y otra con 50 presentaciones y 10 fallos
    When se calcula el ranking
    Then la primera aparece antes que la segunda (100% > 20%)

  Scenario: Materia sin ninguna pregunta presentada
    Given una materia sin ninguna Respuesta vigente
    When un Docente consulta el ranking
    Then recibe 200 con lista vacía

  Scenario: Comisión que no pertenece a la materia
    Given una comisión de otra materia
    When un Docente hace GET .../ranking-preguntas-falladas?comision_id={esa comisión}
    Then recibe 422

  Scenario: Rol distinto de Docente
    Given un Estudiante autenticado
    When hace GET /analytics/materias/X/ranking-preguntas-falladas
    Then recibe 403
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — reusa exactamente la fuente de `US-4.2.4`, solo cambia la clave de agrupación; el
  único cambio de contrato es ampliar `MetadatoPreguntaResumen` con `enunciado`.

**Capa(s) afectadas:**
- [ ] Entities — sin cambios
- [x] Use Cases — `ObtenerRankingPreguntasFalladasUseCase` (nuevo)
- [x] Interface Adapters — `AnalyticsController` (método nuevo)
- [x] Frameworks — `PreguntaMetadatoConsultaPort`/DTO ampliado con `enunciado` (adapter
  existente, ampliado); `analytics_router.py` agrega el `GET`
- [ ] Frontend — no aplica a esta US (`US-ADJ-50`)

---

## Fuente de verdad UX

No aplica a esta US — endpoint backend puro. La pantalla que lo consume
(`#doc-ranking-preguntas`) se especifica en `US-ADJ-50` contra
`docs/design/ux/wireframes-analytics.md` §3.4 (umbrales de color ≥50%/20-49%/<20%, mismo
criterio de `US-4.2.6`).

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/analytics/entities/ports/pregunta_metadato_consulta_port.py` | `MetadatoPreguntaResumen` gana el campo `enunciado: str` |
| `src/analytics/frameworks/adapters/pregunta_metadato_consulta_port_in_process.py` | Trae `enunciado` en la misma consulta por lote |
| `src/analytics/use_cases/obtener_ranking_preguntas_falladas.py` | Nuevo |
| `src/analytics/interface_adapters/controllers/analytics_controller.py` | Método nuevo |
| `src/analytics/frameworks/api/analytics_router.py` | Agrega `GET /materias/{materia_id}/ranking-preguntas-falladas` |
| `tests/unit/inc5-adj/` y `tests/integration/inc5-adj/` | Tests del Use Case y del endpoint (agregado total, por comisión, orden por tasa vs. conteo, vacío, 422, 403) |

---

## Referencias

- Modelo de dominio: `docs/design/domain/BC-analytics-modelo.md` §8.2/§8.3
- Wireframes: `docs/design/ux/wireframes-analytics.md` §3.4
- Depende de: `US-4.2.2` (#241), `US-4.2.3` (#242), `US-4.2.4` (#243)
- Consumida por: `US-ADJ-50`
- Candidatas: `docs/plans/inc5-adj/inc5-adj-candidatas.md` §Iteración 4
- Issue: [#356](https://github.com/vvalotto/cognion/issues/356)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
