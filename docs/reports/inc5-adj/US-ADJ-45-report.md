# Reporte de Implementación: US-ADJ-45 - Docente consulta la evolución temporal de aciertos

## Información General

| Campo | Valor |
|-------|-------|
| **Historia de Usuario** | US-ADJ-45 |
| **Título** | Docente consulta la evolución temporal de aciertos |
| **Producto** | analytics |
| **Prioridad** | Segunda US de la Iteración 4 del Incremento 5-ADJ — implementada junto con `US-ADJ-46`/`47` en una sola ejecución/PR |
| **Puntos estimados** | 5 |
| **Fecha inicio** | 2026-09-14 |
| **Fecha fin** | 2026-09-14 |
| **Tiempo real** | 35.2 min (tracking automático) |
| **Estado** | ✅ COMPLETADO |

---

## Resumen Ejecutivo

Segunda US de la Iteración 4 del Incremento 5-ADJ: el Docente puede ver un gráfico de evolución
del % de aciertos de un estudiante puntual (`GET .../estudiantes/{id}/evolucion-temporal`) y de
su comisión (`GET .../comisiones/{id}/evolucion-temporal`), ambos ordenados cronológicamente y
con el título de cada actividad como etiqueta del eje X (RF-21).

**Gap detectado en la spec, resuelto en Fase 3:** `EvaluacionDesempenoResumen` no traía el
título de la actividad — se amplió `EvaluacionDesempenoConsultaPort` con
`obtener_titulos_actividades`, que reusa `ActividadEvaluativaPeriodoAbierto.reconstruir()`
(mismo criterio que `listar_actividades_abiertas`, `US-ADJ-44`) para reflejar el título
*actual*, no el de creación (`TituloActividadModificado`).

**Corrección de diseño en Fase 7:** `ObtenerEvolucionTemporalComisionUseCase.execute` superó
el umbral de complejidad ciclomática (11/10) al combinar agrupación + promedio + orden en un
solo método. Corregido extrayendo `_acumular_por_actividad`/`_puntos_ordenados` a funciones de
módulo, bajando a CC 5.

Esta US es solo backend — el frontend (`EvolucionTemporal.tsx`) queda para `US-ADJ-49`.

---

## Componentes Implementados

### Código Fuente (BC Analytics)

- ✅ `src/analytics/entities/ports/evaluacion_desempeno_consulta_port.py` — método abstracto
  `obtener_titulos_actividades(actividad_ids)` agregado
- ✅ `src/analytics/frameworks/adapters/evaluacion_desempeno_consulta_port_in_process.py` —
  implementación + función de módulo `_streams_de_actividades` (resuelve por id exacto, más
  liviano que filtrar por materia)
- ✅ `src/analytics/use_cases/obtener_evolucion_temporal_estudiante.py` — nuevo,
  `ObtenerEvolucionTemporalEstudianteUseCase` + `EvolucionTemporalPunto`
- ✅ `src/analytics/use_cases/obtener_evolucion_temporal_comision.py` — nuevo,
  `ObtenerEvolucionTemporalComisionUseCase` + `EvolucionTemporalComisionPunto`, con
  `_acumular_por_actividad`/`_puntos_ordenados` como funciones de módulo (fix de CC)
- ✅ `src/analytics/interface_adapters/controllers/analytics_controller.py` — 2 métodos
  nuevos, constructor gana los 5° y 6° Use Case del BC
- ✅ `src/analytics/frameworks/dependencies.py` — cablea los 2 Use Case nuevos
- ✅ `src/analytics/frameworks/api/schemas.py` — `EvolucionTemporalPuntoResponse`,
  `EvolucionTemporalComisionPuntoResponse`
- ✅ `src/analytics/frameworks/api/analytics_router.py` — 2 endpoints nuevos (rol `docente`)

**Total archivos de producción modificados/creados:** 8 (2 nuevos, 6 modificados)

---

### Tests

#### Tests Unitarios
- ✅ `tests/unit/inc4/test_obtener_evolucion_temporal_estudiante.py` — 5 tests (nuevo)
- ✅ `tests/unit/inc4/test_obtener_evolucion_temporal_comision.py` — 6 tests (nuevo)
- ✅ `tests/unit/inc4/test_analytics_controller.py`, `test_obtener_desempeno_estudiante.py`,
  `test_obtener_desempeno_por_comision.py`, `test_obtener_tasa_error_por_tema.py` — 5 fakes
  ampliados con `obtener_titulos_actividades` (método abstracto nuevo), 2 tests de delegación
  nuevos

**Total tests unitarios del proyecto:** 523/523 pasando (100% coverage en `src/analytics`)

#### Tests de Integración
- ✅ `tests/integration/inc4/test_evaluacion_desempeno_consulta_port.py` —
  `TestObtenerTitulosActividades`, 5 tests nuevos contra Postgres real (incluye título
  modificado por `TituloActividadModificado`)
- ✅ `tests/integration/inc4/test_analytics_router_evolucion_temporal.py` — 9 tests nuevos
  (ambos endpoints completos vía `AsyncClient`)

**Total tests de integración del proyecto:** 368/368 pasando

#### Escenarios BDD
- ✅ `tests/features/inc5-adj/US-ADJ-45-evolucion-temporal.feature` — 6 escenarios
- ✅ `tests/step_defs/inc4/test_us_adj_45_steps.py` — steps nuevo

**Total escenarios BDD del proyecto:** 257/257 pasando

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **Pylint** | 9.92/10 | ≥ 8.0 | ✅ |
| **Complejidad Ciclomática (máx/función)** | 9 | ≤ 10 | ✅ |
| **Índice Mantenibilidad (mín/archivo)** | 50.52 | > 20 | ✅ |
| **Coverage** (entities/use_cases/interface_adapters) | 100% | ≥ 95% | ✅ |
| **mypy** (`src/` completo) | 0 errores | 0 errores | ✅ |
| **CodeGuard** (8 archivos modificados/agregados) | 7 errores, 86 warnings | 0 CRITICAL | ✅ |

Fuente completa: `quality/reports/inc5-adj/US-ADJ-45-quality.json`.

### Detalle de CodeGuard

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 8 |
| PEP8 | 0 | 1 | 7 |
| Complexity | 0 | 0 | 8 |
| DeadCode | 7 | 69 | 1 |
| Maintainability | 0 | 0 | 8 |
| Pylint | 0 | 0 | 8 |
| Spelling | 0 | 16 | 1 |
| Types | 0 | 0 | 7 |
| UnusedImports | 0 | 0 | 8 |

Los 7 errores de `DeadCode` son falso positivo de `vulture` sobre los parámetros de los 4
métodos abstractos de `EvaluacionDesempenoConsultaPort` — mismo patrón ya aceptado en
`US-ADJ-44`.

---

## Criterios de Aceptación

- [x] Serie individual con 3 evaluaciones — 3 puntos ordenados cronológicamente, con título
- [x] Serie de comisión con participación parcial — promedia solo entre quienes finalizaron
- [x] Estudiante sin evaluaciones finalizadas — 200 con lista vacía
- [x] Comisión que no pertenece a la materia — 422
- [x] Sin autenticación — 401
- [x] Rol distinto de Docente — 403

**Estado:** 6/6 cumplidos

---

## Desafíos y Soluciones

### Desafío 1: CC 11/10 detectado recién en Fase 7

**Descripción:** `ObtenerEvolucionTemporalComisionUseCase.execute` combinaba agrupar por
actividad, calcular promedio y ordenar por fecha mínima en un solo método — Fase 3/4 no lo
detectó porque pylint/CC no corren ahí, solo en Fase 7.

**Solución:** Extraer `_acumular_por_actividad` (agrupación) y `_puntos_ordenados`
(cálculo + orden) a funciones de módulo, mismo criterio de extracción ya aplicado en todo el
adapter del BC.

**Aprendizaje:** Un Use Case con más de un paso de agregación (agrupar + calcular + ordenar)
es candidato a extracción a función de módulo desde el diseño en Fase 2, no solo cuando
`DesignReviewer` lo marca en el pre-push.

---

### Desafío 2: Contención de base de datos con una suite corriendo en background

**Descripción:** Correr `pytest tests/integration/` en background mientras se ejecutaban los
tests BDD de esta misma US (ambos contra la misma Postgres local) produjo 4 fallos falsos
(`ForeignKeyViolationError`) que desaparecieron al re-ejecutar en aislamiento.

**Solución:** Confirmar que ninguna otra suite esté corriendo contra la misma base antes de
lanzar tests que además truncan tablas en su fixture `autouse`.

**Aprendizaje:** No paralelizar corridas de tests que comparten la base Postgres local, ni
siquiera dentro de la misma sesión de trabajo.

---

## Documentación Actualizada

- [x] Docstrings agregados/actualizados en los 8 archivos tocados
- [x] `docs/plans/US-ADJ-45-plan.md` completado con estado, métricas y lecciones aprendidas
- [x] `CHANGELOG.md` actualizado (`[Unreleased]`)
- [x] `quality/reports/inc5-adj/US-ADJ-45-quality.json` y `-codeguard.json` generados
- [ ] `docs/plans/inc5-adj/inc5-adj-candidatas.md`/`CLAUDE.md` — se actualizan al cierre de
  sesión (`/checkpoint`), no en esta fase

---

## Tiempo Invertido

| Fase | Tiempo Real |
|------|-------------|
| Fase 0 — Validación de Contexto | 21 s |
| Fase 1 — Generación de Escenarios BDD | 18 s |
| Fase 2 — Plan de Implementación | 59 s |
| Fase 3 — Implementación (5 tareas) | 490 s |
| Fase 4 — Tests Unitarios | 145 s |
| Fase 5 — Tests de Integración | 482 s |
| Fase 6 — Validación BDD | 343 s |
| Fase 7 — Quality Gates (incluye fix de CC) | 639 s |
| Fase 8 — Documentación | 54 s |
| **TOTAL (Fases 0-8)** | **2251 s (≈ 37.5 min)** |

---

## Lecciones Aprendidas

### Lo que Funcionó Bien

1. Aplicar desde el arranque de Fase 3 la lección de `US-ADJ-44` (actualizar todos los
   `Fake*(EvaluacionDesempenoConsultaPort)` en la misma tarea que amplía el puerto) evitó
   repetir el ciclo de fallos posteriores en Fase 4 — 0 fallos de fakes rotos esta vez.
2. Reusar `ActividadEvaluativaPeriodoAbierto.reconstruir()` para resolver el título actual
   fue directo por ya tener el precedente de `US-ADJ-44`.

### Lo que Puede Mejorar

1. Anticipar en el plan de Fase 2 qué Use Case tiene más de un paso de agregación, para
   extraer a función de módulo desde el diseño en vez de corregir recién en Fase 7.

### Recomendaciones para Próximas Historias

1. `US-ADJ-46` (ranking de preguntas falladas) reagrupa por `pregunta_id` en vez de tema —
   mismo riesgo de CC si el agregado + ordenamiento no se separa desde el plan.

---

## Próximos Pasos

### Historias Relacionadas

- [ ] `US-ADJ-46` — Docente consulta el ranking de preguntas más falladas (RF-22, backend)
- [ ] `US-ADJ-49` — Docente ve la evolución temporal (RF-21, frontend — consume esta US)

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-09-14
