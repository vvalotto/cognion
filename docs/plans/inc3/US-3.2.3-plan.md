# Plan de Implementación: US-3.2.3 - Estudiante finaliza su evaluación y ve la revisión completa

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion — BC Actividad Evaluativa
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-08-27

## Métricas de Tiempo (tracking real, PRIN-001: no comparan contra estimación humana)

| Fase | Tiempo real |
|------|-------------|
| 0 — Contexto | 2.6 min |
| 1 — Escenarios BDD | 0.3 min |
| 2 — Plan de implementación | 3.8 min |
| 3 — Implementación guiada por tareas | 6.0 min |
| 4 — Tests unitarios | 4.7 min |
| 5 — Tests de integración | 6.6 min |
| 6 — Validación BDD | 2.8 min |
| 7 — Quality gates | 5.8 min |
| 8 — Documentación | — |
| **Total** | **~34 min** |

## Lecciones aprendidas

- ✅ Separar `ObtenerRevisionEvaluacionUseCase` (query) en un `RevisionController` propio desde
  el diseño (Fase 2) evitó repetir el CRITICAL de CBO que salió 3 veces en Incremento 2 —
  mismo criterio ya validado en `US-2.1.7`/`US-2.2.2`/`US-2.2.3`/`US-3.2.2`.
- ✅ `PreguntaConsultaPort.obtener_detalle_correccion()` (nuevo método sobre un puerto
  existente, no un puerto nuevo) resolvió la necesidad de exponer texto + respuesta correcta
  sin ensanchar el contrato más de lo necesario.
- 💡 `codeguard` acotado a los archivos modificados (CLAUDE.md, Fase 7) detectó 5 líneas
  largas (>100 cols) que `black` no había normalizado solo — reformatear con `black` antes de
  correr `codeguard` evita ese ida-y-vuelta.

## Componentes a Implementar

### 1. Entities

- [x] `src/actividad_evaluativa/entities/errors.py`
  - `EvaluacionNoFinalizada`: se rechaza `ObtenerRevisionEvaluacion` sobre `Evaluacion` no `Finalizada`
- [x] `src/actividad_evaluativa/entities/eventos.py`
  - `EvaluacionFinalizada(evaluacion_id, actor, ocurrido_en)` — mismo shape que `EvaluacionSuspendida`
- [x] `src/actividad_evaluativa/entities/evaluacion.py`
  - `validar_para_finalizar()` (función de módulo `_validar_para_finalizar`, mismo criterio que `_validar_para_suspender`/`_validar_para_reanudar`): solo rechaza `EvaluacionYaFinalizada`
  - `respuesta_vigente_de(pregunta_id) -> Respuesta | None`: la de `confirmada_en` más reciente entre las que matchean `pregunta_id` (INV-AE-09), `None` si no hay ninguna
  - `_aplicar_evento`: nueva rama `EvaluacionFinalizada` → `estado = FINALIZADA`
- [x] `src/actividad_evaluativa/entities/ports/pregunta_consulta_port.py`
  - VO `DetalleCorreccionPregunta(texto: str, contenido_correcto: dict[str, Any])`
  - Método abstracto `obtener_detalle_correccion(pregunta_id: UUID) -> DetalleCorreccionPregunta`
- [x] `src/actividad_evaluativa/entities/revision_evaluacion.py` (nuevo)
  - `DetallePreguntaRevision` (frozen dataclass): `pregunta_id`, `orden`, `texto`, `respondida: bool`, `contenido_propio: dict[str, Any] | None`, `es_correcta: bool`, `contenido_correcto: dict[str, Any] | None`
  - `RevisionEvaluacion` (frozen dataclass): `evaluacion_id`, `cantidad_preguntas`, `cantidad_correctas`, `cantidad_incorrectas`, `detalle: list[DetallePreguntaRevision]`

### 2. Frameworks — Adapter de Banco de Preguntas

- [x] `src/actividad_evaluativa/frameworks/adapters/pregunta_consulta_port_in_process.py`
  - Implementa `obtener_detalle_correccion`: resuelve `PreguntaPlantilla` por id, arma `contenido_correcto` según tipo concreto (`{"opcion_indice": indice_correcto}` para `PreguntaPlantillaOpcionMultiple`, `{"valor": pregunta.respuesta_correcta}` para `PreguntaPlantillaVerdaderoFalso`, mismo criterio de `evaluar_correccion`), `texto = pregunta.texto`

### 3. Use Cases

- [x] `src/actividad_evaluativa/use_cases/finalizar_evaluacion.py` (nuevo)
  - `FinalizarEvaluacionUseCase(event_store)` — mismo esqueleto que `SuspenderEvaluacionUseCase`: `load` → ownership check → `validar_para_finalizar` → `append(EvaluacionFinalizada, actor="estudiante")`
- [x] `src/actividad_evaluativa/use_cases/obtener_revision_evaluacion.py` (nuevo)
  - `ObtenerRevisionEvaluacionUseCase(pregunta_consulta, event_store)`
  - `load` evaluación, ownership check, si `estado != FINALIZADA` → `EvaluacionNoFinalizada`
  - Por cada `PreguntaAsignada` (en su `orden`): `respuesta_vigente_de`, `obtener_detalle_correccion`; arma `DetallePreguntaRevision` (incluye `contenido_correcto` solo si `not respondida or not es_correcta`)
  - Agrega los conteos (`cantidad_correctas`, no respondida cuenta como incorrecta) y devuelve `RevisionEvaluacion`

### 4. Interface Adapters

- [x] `src/actividad_evaluativa/interface_adapters/controllers/evaluaciones_controller.py`
  - Inyecta `FinalizarEvaluacionUseCase`, agrega método `finalizar_evaluacion(evaluacion_id, estudiante_id)`
- [x] `src/actividad_evaluativa/interface_adapters/controllers/revision_controller.py` (nuevo)
  - `RevisionController(obtener_revision_evaluacion)` con método `obtener_revision(evaluacion_id, estudiante_id)` — separado de `EvaluacionesController` (comando vs. query, mismo criterio ya aplicado en `US-2.1.7`/`US-2.2.2`/`US-2.2.3` para no repetir el CRITICAL de CBO)

### 5. Frameworks — API

- [x] `src/actividad_evaluativa/frameworks/api/schemas.py`
  - `DetallePreguntaRevisionResponse`, `RevisionEvaluacionResponse`
- [x] `src/actividad_evaluativa/frameworks/api/evaluaciones_router.py`
  - `POST /evaluaciones/{evaluacion_id}/finalizar` (rol `estudiante`) — 404 `EvaluacionNoExiste`, 422 `EvaluacionYaFinalizada`
- [x] `src/actividad_evaluativa/frameworks/api/revision_router.py` (nuevo)
  - `GET /evaluaciones/{evaluacion_id}/revision` (rol `estudiante`) — 404 `EvaluacionNoExiste`, 422 `EvaluacionNoFinalizada`

### 6. Integración

- [x] `src/actividad_evaluativa/frameworks/dependencies.py`
  - `get_evaluaciones_controller`: agrega `FinalizarEvaluacionUseCase(event_store)`
  - `get_revision_controller(session)` (nuevo): arma `RevisionController` con `ObtenerRevisionEvaluacionUseCase(pregunta_consulta, event_store)`
- [x] `src/app.py`
  - Importa y registra `revision_router`

**Estado:** 16/16 tareas completadas
