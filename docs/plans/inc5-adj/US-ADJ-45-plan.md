# Plan de Implementación: US-ADJ-45 - Docente consulta la evolución temporal de aciertos

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion (BC Analytics)
**Estado:** ✅ COMPLETADO — 2026-09-14
**Tiempo real (tracking):** 34 min (Fases 0 a 7), 5/5 tareas completadas
**Quality gates:** APROBADO (pylint 9.92/10, CC máx 9, MI mín 50.52, coverage 100%) —
`quality/reports/inc5-adj/US-ADJ-45-quality.json`
**Tests:** 1148/1148 (unit + integration + BDD) en verde

## Lecciones aprendidas

- ✅ Aplicar desde el arranque de Fase 3 la lección de `US-ADJ-44` (actualizar todos los
  `Fake*(EvaluacionDesempenoConsultaPort)` en la misma tarea que amplía el puerto) evitó
  repetir el ciclo de fallos posteriores en Fase 4.
- ⚠️ `ObtenerEvolucionTemporalComisionUseCase.execute` superó CC 10 (11) recién al correr
  Fase 7 — el plan no anticipó que agrupar+promediar+ordenar en un solo método cruzaría el
  umbral. Corregido extrayendo `_acumular_por_actividad`/`_puntos_ordenados` a funciones de
  módulo. Para `US-ADJ-46`/`47` conviene planificar la extracción a función de módulo *antes*
  de escribir el Use Case si tiene más de un paso de agregación (agrupar + calcular + ordenar).
- 💡 Correr una suite de integración/BDD pesada en background mientras se ejecutan otros tests
  contra la misma base Postgres produce fallos falsos (`ForeignKeyViolationError` por
  contención) — no compartir la base entre corridas concurrentes de tests, incluso dentro de
  la misma sesión.

## Decisión de diseño previa

`obtener_titulos_actividades` necesita `titulo` de `ActividadEvaluativaPeriodoAbierto` (puede
haber cambiado por `TituloActividadModificado`) — mismo criterio ya aplicado en `US-ADJ-44`:
reusa `ActividadEvaluativaPeriodoAbierto.reconstruir()` en vez de leer solo el primer evento.
Se resuelve por `actividad_id` directo (`aggregate_id.in_(...)`), no por `materia_id`, porque
ya se conocen los ids exactos desde los resúmenes de evaluación — más preciso y liviano que
filtrar por materia como hace `_streams_actividad_de_materia`.

**Lección aplicada de US-ADJ-44:** al agregar el método al puerto en la Tarea 1, en la misma
tarea se actualizan todos los `Fake*(EvaluacionDesempenoConsultaPort)` existentes en
`tests/unit/` (4 archivos: `test_obtener_tasa_error_por_tema.py`,
`test_obtener_desempeno_estudiante.py` ×2 fakes, `test_analytics_controller.py`,
`test_obtener_desempeno_por_comision.py`) — no se difiere a un fix posterior en Fase 4.

## Componentes a Implementar

### 1. Port y Adapter
- [x] `src/analytics/entities/ports/evaluacion_desempeno_consulta_port.py` — método abstracto
  `obtener_titulos_actividades(actividad_ids: list[UUID]) -> dict[UUID, str]`
- [x] `src/analytics/frameworks/adapters/evaluacion_desempeno_consulta_port_in_process.py` —
  implementación + función de módulo nueva `_streams_de_actividades(session, actividad_ids)`
  (mismo patrón de extracción a función de módulo que el resto del archivo, por WMC)
- [x] Actualizar los 5 `Fake*(EvaluacionDesempenoConsultaPort)` de `tests/unit/` con el método
  nuevo (`raise NotImplementedError` salvo donde se ejercite)

### 2. Use Cases
- [x] `src/analytics/use_cases/obtener_evolucion_temporal_estudiante.py` (nuevo) —
  `EvolucionTemporalPunto` (dataclass: `actividad_id`, `titulo_actividad`, `finalizada_en`,
  `porcentaje_acierto`), `ObtenerEvolucionTemporalEstudianteUseCase` — reusa
  `listar_evaluaciones_finalizadas` (ya existente), ordena por `finalizada_en` ascendente
- [x] `src/analytics/use_cases/obtener_evolucion_temporal_comision.py` (nuevo) —
  `EvolucionTemporalComisionPunto` (dataclass: `actividad_id`, `titulo_actividad`,
  `porcentaje_aciertos_promedio`), `ObtenerEvolucionTemporalComisionUseCase` — agrupa por
  `actividad_id` entre los estudiantes del roster, ordena por `min(finalizada_en)` del grupo

### 3. Controller, DI, Schemas y Router
- [x] `src/analytics/interface_adapters/controllers/analytics_controller.py` — 2 métodos
  nuevos, constructor gana los 2 Use Case
- [x] `src/analytics/frameworks/dependencies.py` — cablea los 2 Use Case nuevos
- [x] `src/analytics/frameworks/api/schemas.py` — `EvolucionTemporalPuntoResponse`,
  `EvolucionTemporalComisionPuntoResponse`
- [x] `src/analytics/frameworks/api/analytics_router.py` —
  `GET /materias/{materia_id}/estudiantes/{estudiante_id}/evolucion-temporal` (valida
  `EstudianteConsultaPort.existe`, mismo patrón que `obtener_desempeno_de_estudiante`) y
  `GET /materias/{materia_id}/comisiones/{comision_id}/evolucion-temporal` (mapea
  `ComisionNoPerteneceAMateria` → 422), ambos rol `docente`

**Estado:** 0/10 tareas completadas
