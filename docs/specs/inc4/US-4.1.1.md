# US-4.1.1: Infraestructura de consulta del BC Analytics

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-4.1`
**Tipo**: `infra backend` (técnica — sin comando/query de negocio propio)
**Agregado principal afectado**: — (BC sin aggregate propio, `BC-analytics-modelo.md` §2)
**Bounded Context**: Analytics

---

## Descripcion (lenguaje de negocio)

Como **equipo de desarrollo**,
quiero **el puerto de consulta y el adapter que le permiten a Analytics leer el event store de
Actividad Evaluativa en modo solo-lectura**
para **que `US-4.1.2` (y toda la Iteración 2) tengan de dónde leer el desempeño de un
estudiante, sin que cada Use Case reimplemente su propia consulta sobre la tabla `events`
ajena**.

---

## Contexto del dominio

### Problema

`src/analytics/` es hoy solo el esqueleto de carpetas de BL-000 (4 capas vacías, sin código de
negocio) — primer código real del BC. A diferencia de Actividad Evaluativa (`US-3.1.1`),
Analytics **no crea su propio event store** — es puramente de lectura (`BC-analytics-modelo.md`
§2): consume el event store que ya existe, escrito por Actividad Evaluativa desde el
Incremento 3.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Port (nuevo) | `EvaluacionDesempenoConsultaPort` | `listar_evaluaciones_finalizadas(estudiante_id, materia_id: UUID \| None) -> list[EvaluacionDesempenoResumen]` — definido en `src/analytics/entities/ports/`, sin conocer SQLAlchemy ni el event store ajeno |
| DTO (nuevo) | `EvaluacionDesempenoResumen` | `evaluacion_id`, `actividad_id`, `materia_id`, `finalizada_en`, `cantidad_correctas`, `cantidad_incorrectas` — solo lo que Analytics necesita, sin exponer el aggregate `Evaluacion` ajeno |
| Adapter (nuevo) | `EvaluacionDesempenoConsultaPortInProcess` | Implementa el puerto consultando directamente `EventoModel` (tabla `events`) de `src.actividad_evaluativa.frameworks.db.models` — vive en `src/analytics/frameworks/adapters/`, único punto de Analytics que importa código de otro BC |

**Decisión de acoplamiento (a diferencia de `MateriaConsultaPortInProcess`/`MateriaPortInProcess`,
que invocan un Use Case de la BC dueña):** no existe en Actividad Evaluativa ningún Use Case que
devuelva "todas las `Evaluacion` finalizadas de un estudiante, con el detalle de correctas/
incorrectas por evaluación" — construirlo ahí solo para que Analytics lo consuma ensancharía un
BC ajeno con una responsabilidad que no es suya (mismo criterio de "no agregar responsabilidad
ajena a un BC existente" ya aplicado repetidas veces en el proyecto). El adapter de Analytics
consulta `EventoModel` directamente, mismo criterio de acoplamiento consciente que `ADR-006` —
lee la tabla compartida (`ADR-004`, `ADR-017`), no importa lógica de negocio de Actividad
Evaluativa. Vive exclusivamente en `frameworks/`, nunca en `entities/` ni `use_cases/`.

**Algoritmo de `listar_evaluaciones_finalizadas` (consulta directa sobre `events`, sin
materializar — `BC-analytics-modelo.md` §2):**
1. Buscar los `aggregate_id` de stream `Evaluacion` cuyo evento `EvaluacionIniciada` tiene
   `payload->>'estudiante_id' = estudiante_id` (y, si `materia_id` viene informado, cuya
   `actividad_id` resuelve a esa materia — ver paso 4).
2. De esos, quedarse solo con los que tienen un evento `EvaluacionFinalizada` (mismo criterio
   que `EvaluacionEstudianteQueryPort.existentes_finalizadas`, `US-3.4.5`) — `finalizada_en` es
   el `occurred_at` de ese evento.
3. Para cada `evaluacion_id`, contar `RespuestaRegistrada` agrupando por `pregunta_id` y
   quedándose con la de `confirmada_en` más reciente (INV-AE-09, respuesta vigente) — de esas,
   contar `es_correcta = true` vs. `false`.
4. Resolver `materia_id`: leer el primer evento (`ActividadEvaluativaCreada`) del stream
   `ActividadEvaluativaPeriodoAbierto` correspondiente al `actividad_id` de cada `Evaluacion` —
   `materia_id` no cambia después de creada la actividad, no hace falta replay completo.

---

## Especificacion del comportamiento

### Precondicion

- Ninguna — primer código del BC. No depende de ninguna otra US de Analytics.
- Requiere que el BC Actividad Evaluativa tenga su tabla `events` ya migrada (`US-3.1.1`,
  cerrada desde el Incremento 3).

### Postcondicion

- `EvaluacionDesempenoConsultaPort.listar_evaluaciones_finalizadas(estudiante_id, materia_id)`
  devuelve la lista de `EvaluacionDesempenoResumen` de ese estudiante — vacía si no tiene
  ninguna `Evaluacion` finalizada.
- Sin `materia_id`, devuelve las de todas las materias (uso interno de `US-4.2.1`/`US-4.2.4` más
  adelante, aunque `US-4.1.2` siempre lo invoca con `materia_id` informado).
- Composition root `src/analytics/frameworks/dependencies.py` creado, con el adapter cableado
  contra la sesión async compartida (`shared/frameworks/db.py`).
- Router base `src/analytics/frameworks/api/analytics_router.py` creado (sin endpoints
  todavía — los agrega `US-4.1.2`) y registrado en `src/app.py`.
- Un test de integración prueba el algoritmo completo contra datos reales de `events`
  (fixtures que simulan `ActividadEvaluativaCreada`/`EvaluacionIniciada`/
  `RespuestaRegistrada`/`EvaluacionFinalizada`, mismo patrón que los tests de
  `SQLAlchemyEvaluacionEstudianteQueryRepository`).

### Invariantes

| ID | Invariante |
|----|------------|
| — | La respuesta vigente por `pregunta_id` es siempre la de `confirmada_en` más reciente (INV-AE-09) — nunca cuenta una respuesta reemplazada por un reintento posterior. |
| — | Una `Evaluacion` sin evento `EvaluacionFinalizada` nunca aparece en el resultado — Analytics solo reporta sobre evaluaciones terminadas (RF-15 no pide progreso parcial). |

---

## Criterios de aceptacion

```gherkin
Feature: Infraestructura de consulta del BC Analytics (US-4.1.1)

  Scenario: Estudiante con evaluaciones finalizadas en la materia
    Given un estudiante con 2 Evaluacion finalizadas en la materia X (una con 8 correctas y
      2 incorrectas, otra con 5 correctas y 3 incorrectas)
    When se llama listar_evaluaciones_finalizadas(estudiante_id, materia_id=X)
    Then el resultado tiene 2 filas con los conteos exactos de cada una

  Scenario: Evaluación EnCurso, sin finalizar
    Given un estudiante con una Evaluacion EnCurso (sin EvaluacionFinalizada) en la materia X
    When se llama listar_evaluaciones_finalizadas(estudiante_id, materia_id=X)
    Then esa Evaluacion no aparece en el resultado

  Scenario: Respuesta con reintentos — cuenta solo la vigente
    Given una Evaluacion finalizada con 2 Respuesta para la misma pregunta_id (la primera
      incorrecta, la segunda —más reciente— correcta)
    When se llama listar_evaluaciones_finalizadas(...)
    Then esa pregunta cuenta como correcta, no como incorrecta

  Scenario: Filtro por materia
    Given un estudiante con Evaluacion finalizadas en dos materias distintas
    When se llama listar_evaluaciones_finalizadas(estudiante_id, materia_id=X)
    Then el resultado solo incluye las de la materia X

  Scenario: Estudiante sin evaluaciones finalizadas
    Given un estudiante sin ninguna Evaluacion finalizada
    When se llama listar_evaluaciones_finalizadas(estudiante_id, materia_id=X)
    Then el resultado es una lista vacía
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — implementa el consumo de solo-lectura ya anticipado en `BC-actividad-evaluativa-
  modelo.md` §6 ("Frontera con Analytics") y detallado en `BC-analytics-modelo.md` §5/§6. La
  única decisión nueva (importar `EventoModel` directamente en vez de invocar un Use Case
  ajeno) queda documentada arriba, no amerita ADR — es la misma categoría de acoplamiento
  consciente que `ADR-006` ya cubre.

**Capa(s) afectadas:**
- [x] Entities — `EvaluacionDesempenoConsultaPort`, `EvaluacionDesempenoResumen`
  (`entities/ports/`)
- [ ] Use Cases — sin Use Case propio (lo consume `US-4.1.2`)
- [ ] Interface Adapters — sin controller propio todavía (`US-4.1.2` lo agrega)
- [x] Frameworks — `EvaluacionDesempenoConsultaPortInProcess`, router base, composition root
- [ ] Frontend — no aplica a esta US (`US-4.1.3`)

---

## Fuente de verdad UX

No aplica — infraestructura backend pura, sin pantalla.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/analytics/entities/ports/evaluacion_desempeno_consulta_port.py` | Nuevo — `EvaluacionDesempenoConsultaPort`, `EvaluacionDesempenoResumen` |
| `src/analytics/frameworks/adapters/evaluacion_desempeno_consulta_port_in_process.py` | Nuevo — implementación sobre `EventoModel` de Actividad Evaluativa |
| `src/analytics/frameworks/api/analytics_router.py` | Nuevo — router base, sin endpoints (los agrega `US-4.1.2`) |
| `src/analytics/frameworks/dependencies.py` | Composition root del BC (arranca vacío de controllers, lo completa `US-4.1.2`) |
| `src/app.py` | Registra `analytics_router` |
| `tests/integration/inc4/test_evaluacion_desempeno_consulta_port.py` | Tests del algoritmo contra fixtures de `events` |

---

## Referencias

- Modelo de dominio: `docs/design/domain/BC-analytics-modelo.md` §2 (sin aggregate propio), §5
  (puertos), §6 (query directa, sin materializar)
- Precedente de patrón: `EvaluacionEstudianteQueryPort`/
  `SQLAlchemyEvaluacionEstudianteQueryRepository` (`US-3.4.5`, consulta directa sobre `events`
  dentro del propio BC), `MateriaConsultaPortInProcess` (`US-2.1.2`, adapter in-process
  cross-BC)
- Consumida por: `US-4.1.2` y toda la Iteración 2
- Candidatas: `docs/plans/inc4/inc4-candidatas.md` §Iteración 1

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
