# Reporte de Implementación: US-4.2.3

## Resumen Ejecutivo

- **Historia de Usuario:** US-4.2.3 — PreguntaMetadatoConsultaPort hacia Banco de Preguntas
- **Puntos estimados:** 2
- **Tiempo real:** ~24 min (suma de fases con tracking activo; PRIN-001 — tiempo real de
  ejecución del agente, no comparable contra estimación humana)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-09-05

---

## Componentes Implementados

### Entities (`src/analytics/entities/`)

- ✅ **`PreguntaMetadatoConsultaPort`**
  (`src/analytics/entities/ports/pregunta_metadato_consulta_port.py`, nuevo) — puerto propio de
  Analytics, único método `obtener_metadatos(pregunta_ids) -> dict[UUID, MetadatoPreguntaResumen]`;
  incluye el DTO nuevo `MetadatoPreguntaResumen` (`unidad_tematica`, `tema`) — copia propia, no
  reexporta `MetadatosPregunta` de Banco de Preguntas

### Frameworks (`src/analytics/frameworks/`)

- ✅ **`PreguntaMetadatoConsultaPortInProcess`**
  (`src/analytics/frameworks/adapters/pregunta_metadato_consulta_port_in_process.py`, nuevo) —
  único punto nuevo de Analytics que importa `src.banco_preguntas`; consulta
  `PreguntaPlantillaModel` en una sola query por lote (`WHERE id IN (...)`), sin filtrar por
  `activa` (el metadato no depende del estado de baja lógica); lote vacío → `{}` sin consultar
  la base
- ✅ **`dependencies.py`** de Analytics (extendido) — `get_pregunta_metadato_consulta_port`, sin
  consumidor todavía (lo cablea `US-4.2.4`)

### Integración

- ✅ Sin migraciones de base de datos — solo lecturas sobre la tabla `pregunta_plantilla`
  existente
- ✅ Sin Use Case nuevo — puerto de infraestructura puro, mismo patrón que `US-4.1.1`/`US-4.2.2`

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint (`src/analytics/`) | 9.60/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 3 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (mín) | 60.90 | > 20 | ✅ |
| Cobertura de Tests (`entities/ports/`, único archivo no excluido) | 100% | ≥ 95% | ✅ |

**Estado General:** ✅ APROBADO (`quality/reports/inc4/US-4.2.3-quality.json`)

> `frameworks/*` está excluido del gate de coverage por `pyproject.toml` (mismo criterio en
> todos los BCs) — el adapter in-process se valida vía 4 tests de integración reales contra
> Postgres + 4 escenarios BDD, no vía el porcentaje de Fase 7.

### Detalle de CodeGuard

> Generado con `--analysis-type full` y `.venv/bin` antepuesto al PATH.

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 3 |
| PEP8 | 0 | 0 | 3 |
| Complexity | 0 | 0 | 3 |
| DeadCode | 1 | 13 | 0 |
| Maintainability | 0 | 0 | 3 |
| Pylint | 0 | 0 | 3 |
| Spelling | 0 | 1 | 2 |
| Types | 0 | 0 | 3 |
| UnusedImports | 0 | 0 | 3 |

Fuente: `quality/reports/inc4/US-4.2.3-codeguard.json`.

El 1 `error` de DeadCode (vulture, 100% confidence) es el parámetro `pregunta_ids` de la firma
del método abstracto `PreguntaMetadatoConsultaPort.obtener_metadatos` — falso positivo ya
documentado en `US-4.1.1`/`US-4.2.2` para el mismo patrón: vulture analiza cada puerto aislado y
no ve que el parámetro se usa en la implementación concreta. Los 13 `warnings` de DeadCode son
el mismo tipo de falso positivo sobre la clase/DTO/adapter (se usan desde otros archivos:
composition root, tests). El `warning` de Spelling (`Comision`→`Commission`) es una palabra en
español mal interpretada por el diccionario en inglés de codespell, ya presente en un docstring
preexistente no tocado por esta US. Verificado con pylint directo contra `src/analytics/`:
9.60/10, sin errores reales — solo `unnecessary-ellipsis` (mismo estilo que el resto de
`entities/ports/*.py`) y `too-few-public-methods` (mismo patrón ya aceptado en
`EstudianteConsultaPort`/`ComisionConsultaPort`).

---

## Tests Implementados

### Tests Unitarios (3 tests nuevos — `tests/unit/inc4/test_pregunta_metadato_consulta_port.py`)

- ✅ `MetadatoPreguntaResumen` es inmutable (frozen dataclass)
- ✅ `MetadatoPreguntaResumen` conserva los valores recibidos
- ✅ `PreguntaMetadatoConsultaPort` es abstracto, no instanciable

### Tests de Integración (4 tests nuevos, contra Postgres real)

`tests/integration/inc4/test_pregunta_metadato_consulta_port_in_process.py`:
- Lote de 3 preguntas existentes → dict completo con metadatos correctos
- Lote con un id inexistente → esa clave no aparece, sin error
- Lote vacío → dict vacío, sin consultar la base
- Pregunta con baja lógica (`activa=false`) → igual aparece en el resultado

### Escenarios BDD (4 escenarios —
`tests/features/inc4/US-4.2.3-pregunta-metadato-query-port.feature`)

Ejercitados end-to-end vía `tests/step_defs/inc4/test_us_4_2_3_steps.py` (steps síncronos con
`asyncio.run`, `ADR-018`).

**Todos los tests pasando:** ✅ 821/821 (suite `unit/` + `integration/` + `step_defs/`
completa, sin regresiones).

---

## Archivos Creados/Modificados

### Código de producción
- `src/analytics/entities/ports/pregunta_metadato_consulta_port.py` (nuevo)
- `src/analytics/frameworks/adapters/pregunta_metadato_consulta_port_in_process.py` (nuevo)
- `src/analytics/frameworks/dependencies.py` (modificado)

### Tests
- `tests/unit/inc4/test_pregunta_metadato_consulta_port.py` (nuevo — 3 tests)
- `tests/integration/inc4/test_pregunta_metadato_consulta_port_in_process.py` (nuevo — 4 tests)
- `tests/features/inc4/US-4.2.3-pregunta-metadato-query-port.feature` (nuevo)
- `tests/step_defs/inc4/test_us_4_2_3_steps.py` (nuevo)

### Documentación
- `docs/plans/inc4/US-4.2.3-context.md`
- `docs/plans/inc4/US-4.2.3-plan.md`
- `docs/reports/inc4/US-4.2.3-report.md` (este archivo)
- `quality/reports/inc4/US-4.2.3-quality.json`
- `quality/reports/inc4/US-4.2.3-codeguard.json`
- `quality/reports/inc4/US-4.2.3-coverage.json`
- `docs/architecture/20-context-map-integrations.md` (modificado — resuelve la relación
  Analytics → Banco de Preguntas que quedaba explícitamente "a definir en Incremento 4")

---

## Criterios de Aceptación

- [x] Lote de preguntas existentes → dict con una entrada por cada `pregunta_id` encontrado,
  metadato correcto
- [x] Lote con un id inexistente → esa clave no aparece en el resultado, sin lanzar error
- [x] Lote vacío → dict vacío, sin consultar la base
- [x] Analytics nunca importa código de `src/banco_preguntas/` directamente —
  `PreguntaMetadatoConsultaPort` es el único punto de acceso
- [x] Una sola consulta por lote (`WHERE id IN (...)`), no una consulta por `pregunta_id`

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] `US-4.2.4` — tasa de error por unidad/tema (RF-17), consume
  `PreguntaMetadatoConsultaPort` de esta US junto con `ComisionConsultaPort` (`US-4.2.2`)
- [ ] `US-4.2.5`/`US-4.2.6` — pantallas "Desempeño por alumno"/"Desempeño por tema" (UI)

---

## Lecciones Aprendidas

- ⚠️ Los tests de integración/BDD que insertan filas en `pregunta_plantilla`/`banco`/`materia`
  necesitan limpieza local propia (autouse fixture) —
  `tests/integration/inc4/conftest.py` solo limpia la tabla `events`, no las tablas de Banco de
  Preguntas. Sin esa limpieza, filas huérfanas rompían tests de otros BCs (violación de FK al
  correr la suite completa: `DELETE FROM banco` fallaba por `pregunta_plantilla` referenciando
  esas filas) — mismo patrón ya usado por `tests/step_defs/inc4/test_us_4_2_2_steps.py`, ahora
  replicado también en el test de integración nuevo. Detectado corriendo la suite completa
  antes de cerrar Fase 7, no con los tests de la propia US en aislamiento.
- 💡 El proyecto no tenía un `QueryPort`/repositorio con búsqueda por lote en Banco de
  Preguntas (`PreguntaRepositoryPort` solo resuelve por `id` individual o filtro completo) — se
  optó por que el adapter in-process de Analytics consulte `PreguntaPlantillaModel` (tabla)
  directamente en vez de ensanchar el puerto de escritura existente, mismo criterio de
  acoplamiento consciente (`ADR-006`) ya usado por `EvaluacionDesempenoConsultaPortInProcess`
  (`US-4.1.1`) contra la tabla `events` de Actividad Evaluativa.
- ✅ Corregir la decisión inicial de "sin BDD" (por ser una US técnica) al revisar el
  precedente real de `US-4.1.1`/`US-4.2.2` — ambas técnicas y ambas con `.feature` — evitó
  desviarse de la convención establecida del proyecto.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-09-05
