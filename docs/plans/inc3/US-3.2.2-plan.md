# Plan de Implementación: US-3.2.2 - Estudiante suspende y reanuda su evaluación

**Patrón:** Clean Architecture BC-first (`clean-architecture-bc`)
**Producto:** actividad_evaluativa
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-08-27

## Componentes a Implementar

### 1. Entities
- [x] `src/actividad_evaluativa/entities/eventos.py`
  - `EvaluacionSuspendida(evaluacion_id, actor, ocurrido_en)` — `actor` fijo `"estudiante"` en
    esta US (`US-3.2.4` lo reutiliza con `"sistema"`)
  - `EvaluacionReanudada(evaluacion_id, ocurrido_en)`
- [x] `src/actividad_evaluativa/entities/errors.py`
  - `EvaluacionYaSuspendida(evaluacion_id)` — `SuspenderEvaluacion` sobre `Suspendida`
  - `EvaluacionNoSuspendida(evaluacion_id)` — `ReanudarEvaluacion` sobre `EnCurso`
- [x] `src/actividad_evaluativa/entities/evaluacion.py`
  - Método `Evaluacion.validar_para_suspender()` — INV-AE-12: `EvaluacionYaSuspendida` si
    `Suspendida`, `EvaluacionYaFinalizada` si `Finalizada`; no valida período (la spec fija que
    suspender siempre debe poder hacerse)
  - Método `Evaluacion.validar_para_reanudar()` — INV-AE-11: `EvaluacionNoSuspendida` si
    `EnCurso`, `EvaluacionYaFinalizada` si `Finalizada`
  - Ambos siguen el mismo criterio de extracción a función de módulo que
    `_validar_para_registrar_respuesta` (no acoplar la entidad a los errores concretos)
  - `reconstruir()`: reproducir `EvaluacionSuspendida`/`EvaluacionReanudada` sobre `estado`
    (mutan solo `estado`, no tocan `respuestas`/`preguntas_asignadas`)

### 2. Use Cases
- [x] `src/actividad_evaluativa/use_cases/suspender_evaluacion.py`
  - `SuspenderEvaluacionUseCase(event_store)` — carga `Evaluacion` por replay, verifica
    pertenencia al estudiante autenticado (`EvaluacionNoExiste` si no), valida INV-AE-12,
    arma `EvaluacionSuspendida`, `append` con concurrencia optimista
- [x] `src/actividad_evaluativa/use_cases/reanudar_evaluacion.py`
  - `ReanudarEvaluacionUseCase(event_store)` — carga `Evaluacion`, valida INV-AE-11, carga la
    `ActividadEvaluativaPeriodoAbierto` y valida `FueraDePeriodo` (mismo patrón que
    `RegistrarRespuestaUseCase`), arma `EvaluacionReanudada`, `append`

### 3. Interface Adapters
- [x] `src/actividad_evaluativa/interface_adapters/controllers/evaluaciones_controller.py`
  - Inyecta `SuspenderEvaluacionUseCase`/`ReanudarEvaluacionUseCase` (pasa de 2 a 4 Use Case)
  - Métodos `suspender_evaluacion(evaluacion_id, estudiante_id)` /
    `reanudar_evaluacion(evaluacion_id, estudiante_id)`, devuelven `Evaluacion` actualizada

### 4. Frameworks
- [x] `src/actividad_evaluativa/frameworks/api/schemas.py`
  - Reutiliza `EvaluacionResponse` existente para ambas respuestas — sin schema nuevo
- [x] `src/actividad_evaluativa/frameworks/api/evaluaciones_router.py`
  - `POST /evaluaciones/{evaluacion_id}/suspender` (rol `estudiante`, 200, mapea
    `EvaluacionNoExiste`→404, `EvaluacionYaSuspendida`/`EvaluacionYaFinalizada`→422)
  - `POST /evaluaciones/{evaluacion_id}/reanudar` (rol `estudiante`, 200, mapea
    `EvaluacionNoExiste`→404, `EvaluacionNoSuspendida`/`EvaluacionYaFinalizada`/
    `FueraDePeriodo`→422)
- [x] `src/actividad_evaluativa/frameworks/dependencies.py`
  - `get_evaluaciones_controller` instancia y pasa los dos Use Case nuevos al controller

## Integración

- [x] Verificar CBO de `EvaluacionesController` tras inyectar el 3° y 4° Use Case (pre-push
  gate, `.githooks/pre-push` — `DesignReviewer --config pyproject.toml`). Si dispara CRITICAL,
  aplicar el mismo criterio ya usado en Incremento 2/3 (tipar el resultado como tipo más
  genérico o separar command/query) **sin** rediseñar preventivamente — el patrón del proyecto
  es corregir recién si el gate lo detecta.
- [x] Confirmar que `RegistrarRespuestaUseCase`/`registrar_respuesta_controller` no requieren
  cambios — `EvaluacionSuspendida` como error de `RegistrarRespuesta` ya existe desde
  `US-3.2.1`, esta US solo agrega las transiciones de estado que lo producen/revierten.

**Estado:** 11/11 tareas completadas

## Métricas de Tiempo

| Fase | Real |
|------|------|
| 0 — Validación de Contexto | 41 s |
| 1 — Escenarios BDD | 36 s |
| 2 — Plan de Implementación | 47 s |
| 3 — Implementación (8 tareas) | 4 min 17 s |
| 4 — Tests Unitarios | 3 min 11 s |
| 5 — Tests de Integración | 3 min 47 s |
| 6 — Validación BDD | 4 min 37 s |
| 7 — Quality Gates | 5 min 17 s |
| **Total (Fases 0-7)** | **~24 min** |

> Nota (PRIN-001): no hay estimación humana previa comparable — el tracking registra tiempo
> real de ejecución del agente, no varianza contra una estimación de esfuerzo humano.

## Lecciones Aprendidas

- ✅ Reutilizar el mismo patrón de `RegistrarRespuestaUseCase`/`IniciarEvaluacionUseCase`
  (carga por replay, valida invariante, arma evento, `append` con concurrencia optimista) hizo
  la implementación de los dos Use Case nuevos directa, sin decisiones de diseño pendientes.
- ✅ Extender `EvaluacionesController` de 2 a 4 Use Case inyectados no disparó CRITICAL de CBO
  en `DesignReviewer` esta vez — a diferencia del patrón repetido en Incremento 2
  (`PreguntasController`/`CuentasController`), este BC todavía tiene margen antes del umbral.
- 💡 Los escenarios BDD que dependen de que un período expire (`FueraDePeriodo`) necesitan un
  margen de tiempo real generoso (`time.sleep`) para no ser flaky por el overhead de las
  llamadas HTTP intermedias (crear materia, pregunta, actividad, estudiante) — 500ms/1.5s
  (patrón de `US-3.2.1`) resultó insuficiente para este escenario con más pasos previos;
  1s/3s + sleep de 4s fue estable.
