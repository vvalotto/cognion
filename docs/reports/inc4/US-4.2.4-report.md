# Reporte de Implementación: US-4.2.4

## Resumen Ejecutivo

- **Historia de Usuario:** US-4.2.4 — Docente consulta la tasa de error por unidad/tema de una materia
- **Puntos estimados:** 3
- **Tiempo real:** ~63 min (suma de fases con tracking activo; PRIN-001 — tiempo real de
  ejecución del agente, no comparable contra estimación humana)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-09-05

---

## Componentes Implementados

### Entities (`src/analytics/entities/`)

- ✅ **`errors.py`** (nuevo) — primer error de dominio propio de Analytics,
  `ComisionNoPerteneceAMateria`
- ✅ **`EvaluacionDesempenoConsultaPort`** (extendido) — nuevo DTO `RespuestaVigente`
  (`pregunta_id`, `estudiante_id`, `es_correcta`) y nuevo método abstracto
  `listar_respuestas_vigentes_de_materia(materia_id, estudiante_ids)`

### Use Cases (`src/analytics/use_cases/`)

- ✅ **`ObtenerTasaErrorPorTemaUseCase`** (nuevo) — compone
  `EvaluacionDesempenoConsultaPort.listar_respuestas_vigentes_de_materia` (`US-4.1.1`/`US-4.2.4`),
  `ComisionConsultaPort.listar_estudiantes` (`US-4.2.2`, solo si `comision_id` viene informado)
  y `PreguntaMetadatoConsultaPort.obtener_metadatos` (`US-4.2.3`); agrupa por
  `(unidad_tematica, tema)`, calcula `tasa_error` sin dividir por cero y ordena descendente

### Interface Adapters (`src/analytics/interface_adapters/`)

- ✅ **`AnalyticsController`** (extendido) — nuevo método `obtener_tasa_error_por_tema`

### Frameworks (`src/analytics/frameworks/`)

- ✅ **`EvaluacionDesempenoConsultaPortInProcess`** (extendido) — implementa
  `listar_respuestas_vigentes_de_materia`; refactor de `_todos_los_streams_evaluacion` como
  helper común y extracción de `_stream_califica_para_materia` (fix de CC 11→7 en Fase 7)
- ✅ **`schemas.py`** (extendido) — `TasaErrorTemaResponse`
- ✅ **`analytics_router.py`** (extendido) — `GET /analytics/materias/{materia_id}/tasa-error-por-tema?comision_id=`, rol `docente`, 422 si la comisión no pertenece a la materia
- ✅ **`dependencies.py`** (extendido) — cablea `ObtenerTasaErrorPorTemaUseCase` con los 3
  puertos ya provistos (`get_comision_consulta_port`/`get_pregunta_metadato_consulta_port` de
  `US-4.2.2`/`US-4.2.3` tenían "sin consumidor todavía" — ahora sí)

### Integración

- ✅ Sin migraciones de base de datos — solo lecturas sobre `events`, `comision`/`usuario` y
  `pregunta_plantilla` existentes
- ✅ `docs/architecture/20-context-map-integrations.md` actualizado — las dos relaciones
  Analytics → Identidad(`Comisión`) y Analytics → Banco de Preguntas quedaban marcadas "sin
  consumidor todavía"; ahora reflejan a `US-4.2.4` como consumidor real

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint (`src/analytics/`) | 9.64/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 9 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (mín) | 52.54 | > 20 | ✅ |
| Cobertura de Tests (`entities/`, `use_cases/`, `interface_adapters/`) | 100% | ≥ 95% | ✅ |

**Estado General:** ✅ APROBADO (`quality/reports/inc4/US-4.2.4-quality.json`)

> `frameworks/*` está excluido del gate de coverage por `pyproject.toml` (mismo criterio en
> todos los BCs) — el adapter y el endpoint se validan vía 12 tests de integración reales
> contra Postgres + 6 escenarios BDD, no vía el porcentaje de Fase 7.

### Detalle de CodeGuard

> Generado con `--analysis-type full` y `.venv/bin` antepuesto al PATH.

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 8 |
| PEP8 | 0 | 2 | 7 |
| Complexity | 0 | 0 | 8 |
| DeadCode | 4 | 45 | 1 |
| Maintainability | 0 | 0 | 8 |
| Pylint | 2 | 0 | 6 |
| Spelling | 0 | 5 | 4 |
| Types | 0 | 0 | 7 |
| UnusedImports | 3 | 0 | 5 |

Fuente: `quality/reports/inc4/US-4.2.4-codeguard.json`.

Los 4 `errors` de DeadCode (vulture, 100% confidence) son los parámetros de los dos métodos
abstractos de `EvaluacionDesempenoConsultaPort` — falso positivo ya documentado en
`US-4.1.1`/`US-4.2.2`/`US-4.2.3`: vulture no reconoce que el parámetro de un método abstracto
se usa en cada implementación concreta. Los 2 `errors` de Pylint y 3 de UnusedImports son
`pylint execution timed out` en corrida en frío — mismo mecanismo de timeout ya documentado en
`CLAUDE.md` para el check de mypy (`vvalotto/software_limpio#70`). Verificado con la fuente de
verdad local, `pylint src/analytics/` completo: 9.64/10, sin errores reales — solo
`unnecessary-ellipsis` (convención del proyecto) y `duplicate-code`/`too-few-public-methods`
(mismos patrones ya aceptados en el resto del BC).

**CC inicial de `listar_respuestas_vigentes_de_materia` fue 11/10 (CRITICAL)** — corregido en
la misma Fase 7 extrayendo `_stream_califica_para_materia`, sin cambio de comportamiento.

---

## Tests Implementados

### Tests Unitarios (14 tests nuevos, 39/39 en `tests/unit/inc4/`, 400/400 en `tests/unit/` completo)

- `tests/unit/inc4/test_obtener_tasa_error_por_tema.py` (9 tests) — agrupamiento, exclusión sin
  metadato, tasa sin dividir por cero, ordenamiento descendente, resolución de `estudiante_ids`
  por comisión, `ComisionNoPerteneceAMateria`
- `tests/unit/inc4/test_analytics_errors.py` (1 test)
- Extensión de `test_evaluacion_desempeno_consulta_port.py` (DTO `RespuestaVigente`),
  `test_evaluacion_desempeno_consulta_port_in_process.py` (función pura
  `_respuestas_vigentes_de_stream`), `test_analytics_controller.py` (nuevo método del
  controller), `test_obtener_desempeno_estudiante.py` (fakes actualizados al método nuevo del
  port)

### Tests de Integración (12 tests nuevos, 43/43 en `tests/integration/inc4/`, 275/275 en
`tests/integration/` completo)

- Extensión de `test_evaluacion_desempeno_consulta_port.py` (6 tests del método nuevo del
  adapter, contra Postgres real)
- `test_analytics_router_tasa_error_por_tema.py` (nuevo, 6 tests) — endpoint completo con
  `Comisión`/`Usuario` (Identidad) y `PreguntaPlantilla` (Banco de Preguntas) reales

### Escenarios BDD (6 escenarios — `tests/features/inc4/US-4.2.4-tasa-error-por-tema.feature`)

Ejercitados end-to-end vía `tests/step_defs/inc4/test_us_4_2_4_steps.py` (steps síncronos con
`asyncio.run`, `ADR-018`).

**Todos los tests pasando:** ✅ 400/400 unit + 275/275 integration + 176/177 step_defs (el
único fallo, `test_us_3_2_1_steps.py::test_rechazo_fuera_del_período_vigente`, es un flaky
preexistente documentado en `CLAUDE.md` — no relacionado con esta US).

---

## Archivos Creados/Modificados

### Código de producción
- `src/analytics/entities/errors.py` (nuevo)
- `src/analytics/entities/ports/evaluacion_desempeno_consulta_port.py` (modificado)
- `src/analytics/frameworks/adapters/evaluacion_desempeno_consulta_port_in_process.py` (modificado)
- `src/analytics/use_cases/obtener_tasa_error_por_tema.py` (nuevo)
- `src/analytics/interface_adapters/controllers/analytics_controller.py` (modificado)
- `src/analytics/frameworks/api/schemas.py` (modificado)
- `src/analytics/frameworks/api/analytics_router.py` (modificado)
- `src/analytics/frameworks/dependencies.py` (modificado)

### Tests
- `tests/unit/inc4/test_obtener_tasa_error_por_tema.py` (nuevo — 9 tests)
- `tests/unit/inc4/test_analytics_errors.py` (nuevo — 1 test)
- `tests/unit/inc4/test_evaluacion_desempeno_consulta_port.py` (modificado)
- `tests/unit/inc4/test_evaluacion_desempeno_consulta_port_in_process.py` (modificado)
- `tests/unit/inc4/test_analytics_controller.py` (modificado)
- `tests/unit/inc4/test_obtener_desempeno_estudiante.py` (modificado)
- `tests/integration/inc4/test_evaluacion_desempeno_consulta_port.py` (modificado — 6 tests nuevos)
- `tests/integration/inc4/test_analytics_router_tasa_error_por_tema.py` (nuevo — 6 tests)
- `tests/features/inc4/US-4.2.4-tasa-error-por-tema.feature` (nuevo)
- `tests/step_defs/inc4/test_us_4_2_4_steps.py` (nuevo)

### Documentación
- `docs/plans/inc4/US-4.2.4-context.md`
- `docs/plans/inc4/US-4.2.4-plan.md`
- `docs/reports/inc4/US-4.2.4-report.md` (este archivo)
- `quality/reports/inc4/US-4.2.4-quality.json`
- `quality/reports/inc4/US-4.2.4-codeguard.json`
- `quality/reports/inc4/US-4.2.4-coverage.json`
- `docs/architecture/20-context-map-integrations.md` (modificado — refleja a `US-4.2.4` como
  consumidor real de `ComisionConsultaPort`/`PreguntaMetadatoConsultaPort`)

---

## Criterios de Aceptación

- [x] Materia con `Evaluacion` finalizadas de 2 comisiones distintas → tasa de error agregada
  de ambas, ordenada descendente
- [x] Acotado a una comisión → tasa calculada solo sobre sus estudiantes
- [x] Materia sin evaluaciones finalizadas → lista vacía
- [x] Comisión que no pertenece a la materia → 422
- [x] Sin JWT válido → 401
- [x] Rol distinto de Docente → 403
- [x] `tasa_error` nunca divide por cero
- [x] Respuestas de preguntas sin metadato resoluble se excluyen sin romper el cálculo

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] `US-4.2.5` — pantalla "Desempeño por alumno" (UI), consume `US-4.2.1`/`US-4.2.2`
- [ ] `US-4.2.6` — pantalla "Desempeño por tema" (UI), consume esta US

---

## Lecciones Aprendidas

- ⚠️ La Fase 2 (plan) omitió `estudiante_id` en el DTO `RespuestaVigente` sin marcarlo como
  desviación explícita frente a la spec y el modelo de dominio (`BC-analytics-modelo.md` §5,
  que sí lo especifica). Detectado en Fase 8 (discovery de documentación de arquitectura), no
  antes. Corregido sin impacto en el Use Case (no lo usa todavía) ni en las métricas de
  calidad. Lección: comparar explícitamente cada campo de un DTO nuevo contra la tabla del
  modelo de dominio, no solo contra lo que el Use Case actual necesita consumir.
- 💡 Extraer el filtro de un `for` con múltiples condiciones a una función pura
  (`_stream_califica_para_materia`) resolvió el único CRITICAL de CC de la US sin tocar el
  comportamiento — mismo patrón de "separar por responsabilidad" ya usado para CBO en
  incrementos anteriores, aplicado acá a CC.
- ✅ Reutilizar los 3 puertos de consulta ya provistos por US anteriores (`US-4.1.1`,
  `US-4.2.2`, `US-4.2.3`) sin ensanchar ninguno confirmó la decisión de diseño de dejarlos sin
  consumidor hasta esta US — el Use Case nuevo no requirió ningún cambio de firma en los
  puertos existentes.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-09-05
