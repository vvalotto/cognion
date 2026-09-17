# Plan de Implementación: US-ADJ-47 - Docente consulta la completitud de una actividad puntual

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion (BC Analytics)

## Decisión de diseño previa

Reusa `_streams_de_actividades(session, {actividad_id})` (ya existente desde `US-ADJ-45`) para
`obtener_actividad_resumen` — mismo cruce hacia `ActividadEvaluativaPeriodoAbierto.reconstruir()`.
`listar_estados_de_actividad` reusa el mismo criterio de reconstrucción, pero sobre
`Evaluacion.reconstruir()` (entidad pura de Actividad Evaluativa) para resolver `estado`
(`EnCurso`/`Suspendida`/`Finalizada`) sin duplicar la máquina de estados.

**Lección aplicada de `US-ADJ-46`:** antes de decidir a qué controller agregar el Use Case
nuevo, correr `designreviewer` local con el 5° Use Case en `AnalyticsInformesController` y
revisar el CBO resultante — si supera el umbral, evaluar un tercer controller en vez de forzarlo.

## Componentes a Implementar

### 1. Entities (error de dominio nuevo)
- [x] `src/analytics/entities/errors.py` — `ActividadNoExiste(actividad_id)` nuevo

### 2. Port y Adapter
- [x] `src/analytics/entities/ports/evaluacion_desempeno_consulta_port.py` — `ActividadResumen`
  (dataclass: `materia_id`, `comisiones_ids: frozenset[UUID]`) + métodos abstractos
  `obtener_actividad_resumen(actividad_id) -> ActividadResumen | None` y
  `listar_estados_de_actividad(actividad_id, estudiante_ids) -> dict[UUID, str]`
- [x] `src/analytics/frameworks/adapters/evaluacion_desempeno_consulta_port_in_process.py` —
  implementación de ambos métodos (reusa `_streams_de_actividades` para el primero; función de
  módulo nueva `_estados_por_estudiante` para el segundo, con `Evaluacion.reconstruir()`)
- [x] Actualizar todos los `Fake*(EvaluacionDesempenoConsultaPort)` de `tests/unit/` con los 2
  métodos nuevos (9 clases + 1 fake inline en `test_obtener_desempeno_estudiante.py`)

### 3. Use Case
- [x] `src/analytics/use_cases/obtener_completitud_por_actividad.py` (nuevo) —
  `CompletitudFila`/`CompletitudResumen`/`CompletitudPorActividad` (dataclasses),
  `ObtenerCompletitudPorActividadUseCase` — resuelve roster (comisión(es) restringida(s) o
  toda la materia), `_detalle_de`/`_resumen_de` como funciones de módulo desde el diseño

### 4. Controller, DI, Schemas y Router
- [x] Decidido tras correr `designreviewer` local: agregar el 5° Use Case a
  `AnalyticsInformesController` disparó CBO=11/10 CRITICAL — se creó un tercer controller,
  `AnalyticsCompletitudController` (un solo Use Case), 0 CRITICAL confirmado tras el split.
  De paso, el mismo `designreviewer` detectó WMC=29/25 CRITICAL en
  `EvaluacionDesempenoConsultaPortInProcess` (los 2 métodos nuevos de Task 2 empujaron la
  clase sobre el umbral) — resuelto extrayendo `_streams_de_estudiante`/`_resumenes_filtrados`
  como funciones de módulo desde `listar_evaluaciones_finalizadas`, WMC baja a 23.
- [x] `src/analytics/frameworks/dependencies.py` — `get_analytics_completitud_controller` nuevo
- [x] `src/analytics/frameworks/api/schemas.py` — `CompletitudFilaResponse`,
  `CompletitudResumenResponse`, `CompletitudPorActividadResponse`
- [x] `src/analytics/frameworks/api/analytics_router.py` —
  `GET /analytics/actividades/{actividad_id}/completitud` (rol `docente`), mapea
  `ActividadNoExiste` → 404

**Estado:** 8/8 tareas completadas
