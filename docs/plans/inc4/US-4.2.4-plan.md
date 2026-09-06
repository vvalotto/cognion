# Plan de Implementación: US-4.2.4 - Docente consulta la tasa de error por unidad/tema de una materia

**Patrón:** Clean Architecture BC-First (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion — BC Analytics

## Componentes a Implementar

### 1. Errores de dominio (entities)
- [x] `src/analytics/entities/errors.py` (nuevo archivo — primer error de dominio propio de Analytics)
  - `ComisionNoPerteneceAMateria(Exception)`: comisión indicada no pertenece a la materia consultada (422)

### 2. Extensión del Port de desempeño (entities)
- [x] `src/analytics/entities/ports/evaluacion_desempeno_consulta_port.py`
  - `RespuestaVigente`: `@dataclass(frozen=True)` con `pregunta_id: UUID`, `es_correcta: bool` — una fila por respuesta vigente (INV-AE-09), sin exponer `estudiante_id` (no hace falta agregar por alumno acá)
  - Nuevo método abstracto `async def listar_respuestas_vigentes_de_materia(self, materia_id: UUID, estudiante_ids: list[UUID] | None) -> list[RespuestaVigente]` — todas las respuestas vigentes de `Evaluacion` finalizadas de la materia, acotadas a `estudiante_ids` si se indica

### 3. Adapter in-process — implementación del método nuevo (frameworks)
- [x] `src/analytics/frameworks/adapters/evaluacion_desempeno_consulta_port_in_process.py`
  - Refactor interno: generalizar `_eventos_evaluacion_del_estudiante` a `_eventos_evaluacion_de_materia(materia_id, estudiante_ids)` — agrupa streams `Evaluacion` por `aggregate_id`, resuelve `materia_id` de cada stream vía `_materia_por_actividad` (ya existente), filtra por `materia_id` y por `estudiante_id in estudiante_ids` si se indica; sin tocar el método existente `listar_evaluaciones_finalizadas` más que reutilizar el helper común
  - Nuevo método `listar_respuestas_vigentes_de_materia`: para cada stream finalizado que matchea, extrae la última `RespuestaRegistrada` por `pregunta_id` (mismo criterio de `_contar_respuestas_vigentes`, pero devolviendo `RespuestaVigente` en vez de solo contar) y aplana en una única lista

### 4. Use Case nuevo (use_cases)
- [x] `src/analytics/use_cases/obtener_tasa_error_por_tema.py`
  - `TasaErrorTema`: `@dataclass(frozen=True)` con `unidad_tematica: str`, `tema: str`, `cantidad_respuestas: int`, `cantidad_incorrectas: int`, `tasa_error: float`
  - `ObtenerTasaErrorPorTemaUseCase.__init__(evaluacion_desempeno_consulta, comision_consulta, pregunta_metadato_consulta)` — compone los 3 puertos existentes (`US-4.1.1`, `US-4.2.2`, `US-4.2.3`), sin puerto ni evento propio
  - `execute(materia_id, comision_id: UUID | None) -> list[TasaErrorTema]`:
    - `comision_id` informado → valida pertenencia con `comision_consulta.listar_comisiones_por_materia(materia_id)` (si no pertenece, `raise ComisionNoPerteneceAMateria`), y resuelve `estudiante_ids` con `listar_estudiantes(comision_id)`
    - `comision_id` ausente → `estudiante_ids = None` (agrega toda la materia)
    - `evaluacion_desempeno_consulta.listar_respuestas_vigentes_de_materia(materia_id, estudiante_ids)`
    - `pregunta_metadato_consulta.obtener_metadatos(...)` sobre los `pregunta_id` únicos de las respuestas obtenidas
    - agrupa por `(unidad_tematica, tema)` excluyendo respuestas cuyo `pregunta_id` no resolvió metadato; calcula `tasa_error = cantidad_incorrectas / cantidad_respuestas` (nunca por cero — grupo sin respuestas no se construye)
    - devuelve ordenado por `tasa_error` descendente

### 5. Controller (interface_adapters) — extensión
- [x] `src/analytics/interface_adapters/controllers/analytics_controller.py`
  - Nuevo parámetro de constructor `obtener_tasa_error_por_tema: ObtenerTasaErrorPorTemaUseCase`
  - Nuevo método `obtener_tasa_error_por_tema(materia_id, comision_id) -> list[TasaErrorTema]`, delega directo en el Use Case (mismo patrón mínimo que los métodos existentes)

### 6. Schemas (frameworks/api)
- [x] `src/analytics/frameworks/api/schemas.py`
  - `TasaErrorTemaResponse`: `unidad_tematica: str`, `tema: str`, `cantidad_respuestas: int`, `cantidad_incorrectas: int`, `tasa_error: float`

### 7. Router (frameworks/api) — nuevo endpoint
- [x] `src/analytics/frameworks/api/analytics_router.py`
  - `GET /analytics/materias/{materia_id}/tasa-error-por-tema?comision_id=`, `dependencies=[Depends(require_docente)]`
  - Captura `ComisionNoPerteneceAMateria` → 422
  - `comision_id: UUID | None = None` como query param opcional

### 8. Integración (composition root)
- [x] `src/analytics/frameworks/dependencies.py`
  - `get_analytics_controller` arma también `ObtenerTasaErrorPorTemaUseCase` con `get_comision_consulta_port`/`get_pregunta_metadato_consulta_port` (ya provistos por `US-4.2.2`/`US-4.2.3`, sin consumidor hasta ahora) y lo inyecta al `AnalyticsController`

**Estado:** 8/8 tareas completadas

## Tests

- Unitarios: `tests/unit/inc4/test_obtener_tasa_error_por_tema.py` (9 tests), `test_analytics_errors.py` (1), extensión de `test_evaluacion_desempeno_consulta_port.py`/`test_evaluacion_desempeno_consulta_port_in_process.py`/`test_analytics_controller.py` — 39/39 en `tests/unit/inc4/`, 400/400 en `tests/unit/` completo, sin regresiones.
- Integración: extensión de `test_evaluacion_desempeno_consulta_port.py` (6 tests nuevos del método del adapter) + `test_analytics_router_tasa_error_por_tema.py` nuevo (6 tests, endpoint completo con Comisión/Usuario/PreguntaPlantilla reales) — 43/43 en `tests/integration/inc4/`.
- BDD: `tests/step_defs/inc4/test_us_4_2_4_steps.py` — 6/6 escenarios de `US-4.2.4-tasa-error-por-tema.feature` en verde.

## Quality Gates

- pylint 9.64/10, CC máx 9 (bajado de 11 tras refactor de `_stream_califica_para_materia` en Fase 7), MI promedio 93.93 (mín 52.54), coverage 100% (`entities/`, `use_cases/`, `interface_adapters/`)
- codeguard: 9/9 checks corridos en modo `full` — `quality/reports/inc4/US-4.2.4-quality.json` detalla los falsos positivos (DeadCode sobre params de método abstracto, timeout de Pylint/UnusedImports en frío)
- Estado: **APROBADO**

## Lecciones Aprendidas

- ⚠️ La Fase 2 (plan) decidió omitir `estudiante_id` de `RespuestaVigente` sin marcarlo como
  desviación explícita frente a la spec — tanto `docs/specs/inc4/US-4.2.4.md` como
  `BC-analytics-modelo.md` §5 especifican la fila del puerto como
  `(pregunta_id, estudiante_id, es_correcta)`. Detectado recién en Fase 8 (discovery de
  documentación de arquitectura) al releer el modelo de dominio contra el código ya
  implementado. Corregido antes de cerrar: agregado el campo al DTO, resuelto del primer
  evento del stream en el adapter, sin impacto en `ObtenerTasaErrorPorTemaUseCase` (no lo usa
  todavía) ni en las métricas de calidad. Lección: al planificar la Fase 2, comparar
  explícitamente cada campo de un DTO nuevo contra la tabla del modelo de dominio (`BC-*-modelo.md`),
  no solo contra lo que el Use Case actual necesita consumir.
