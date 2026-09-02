# Plan de Implementación: US-3.2.4 - VerificadorDeVencimientos

**Patrón:** Clean Architecture BC-first (`entities → use_cases → interface_adapters → frameworks`)
**Producto:** cognion (BC Actividad Evaluativa)
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-08-27
**Tiempo real (tracker):** ~33 min efectivos (Fases 0-8)

Referencia de diseño completa: `docs/specs/inc3/US-3.2.4.md` (decisiones 1-4 ya confirmadas
con Víctor 2026-08-27: query de lectura sobre `events`, cadencia 120s, umbral 15 min).

## Componentes a Implementar

### 1. Entities/Ports — query de solo lectura

- [ ] `src/actividad_evaluativa/entities/ports/evaluacion_activa_query_port.py`
  - VO `EvaluacionActivaResumen(evaluacion_id, actividad_id, estado, ultima_actividad_en)`
  - `EvaluacionActivaQueryPort(ABC)` con `async def listar_no_finalizadas(self) -> list[EvaluacionActivaResumen]`
  - Sin dependencias externas (pura, como el resto de `entities/ports/`)

### 2. Use Cases — extensión de los dos existentes

- [ ] `src/actividad_evaluativa/use_cases/suspender_evaluacion.py`
  - `execute()` gana `estudiante_id: UUID | None = None, *, actor: str = "estudiante"`
  - Con `actor == "estudiante"` (default): comportamiento idéntico a hoy — `estudiante_id`
    requerido, chequeo de pertenencia, `EvaluacionYaSuspendida`/`EvaluacionYaFinalizada` se
    propagan
  - Con `actor == "sistema"`: sin chequeo de pertenencia; `EvaluacionYaSuspendida`/
    `EvaluacionYaFinalizada` se capturan y el método retorna sin reemitir evento (no-op)
  - `EvaluacionSuspendida(evaluacion_id=..., actor=actor)` — ya no hardcodea `"estudiante"`
- [ ] `src/actividad_evaluativa/use_cases/finalizar_evaluacion.py`
  - Mismo cambio que `suspender_evaluacion.py`, con `EvaluacionYaFinalizada` como único error a
    capturar en modo `actor == "sistema"`

### 3. Use Case nuevo — la Policy

- [ ] `src/actividad_evaluativa/use_cases/verificar_vencimientos.py`
  - `VerificarVencimientosUseCase(evaluacion_activa_query, event_store, suspender_evaluacion, finalizar_evaluacion, umbral_inactividad: timedelta)`
  - `async def execute(self) -> ResumenVerificacion` (VO simple: `suspendidas: int, finalizadas: int`)
  - Regla 1: para cada resumen con `estado == EN_CURSO` y `(ahora - ultima_actividad_en) > umbral_inactividad` → `suspender_evaluacion.execute(evaluacion_id, actor="sistema")`
  - Regla 2: para cada resumen con `estado in (EN_CURSO, SUSPENDIDA)`, resuelve `fecha_cierre` de su `actividad_id` (cachea por `actividad_id` dentro de la misma corrida para no repetir `event_store.load` — ver Decisión de diseño 4 de la spec: lee solo el primer evento del stream, `cerrada_manualmente` asumido `False`); si `fecha_cierre < ahora` → `finalizar_evaluacion.execute(evaluacion_id, actor="sistema")`
  - Sin comando ni evento propio — solo orquesta los dos Use Case existentes

### 4. Frameworks — implementación del port de query

- [ ] `src/actividad_evaluativa/frameworks/adapters/evaluacion_activa_query_repository.py`
  - `SQLAlchemyEvaluacionActivaQueryRepository(session)` implementa `EvaluacionActivaQueryPort`
  - `listar_no_finalizadas()`: `SELECT * FROM events WHERE aggregate_type = 'Evaluacion' ORDER BY aggregate_id, sequence_number`, agrupa en memoria por `aggregate_id` y por cada grupo deriva:
    - `actividad_id` del payload del primer evento (`EvaluacionIniciada`)
    - `estado` según el `event_type` del último evento del grupo (mapeo directo, sin reconstruir el aggregate completo — más liviano que `Evaluacion.reconstruir`)
    - `ultima_actividad_en` = `occurred_at` del evento más reciente de tipo `EvaluacionIniciada`/`RespuestaRegistrada`/`EvaluacionReanudada` dentro del grupo
    - Descarta el grupo si `estado == Finalizada`
  - Extraer la función de agrupamiento/derivación a una función de módulo pura y testeable por separado (mismo criterio de `_aplicar_evento` en `entities/evaluacion.py`, mantiene la CC del método async bajo control)

### 5. Settings — parámetros de configuración

- [ ] `src/settings.py`
  - `verificador_vencimientos_cadencia_segundos: int = 120`
  - `verificador_vencimientos_umbral_inactividad_minutos: int = 15`

### 6. Dependencies — factory sin FastAPI `Depends`

- [ ] `src/actividad_evaluativa/frameworks/dependencies.py`
  - `def build_verificar_vencimientos_use_case(session: AsyncSession) -> VerificarVencimientosUseCase` — recibe la sesión directamente (no `Annotated[..., Depends(...)]`, porque corre fuera del ciclo request/response), arma `SQLAlchemyEvaluacionActivaQueryRepository`, `SQLAlchemyEventStore`, `SuspenderEvaluacionUseCase`, `FinalizarEvaluacionUseCase` y el `timedelta` desde `settings.verificador_vencimientos_umbral_inactividad_minutos`

### 7. Integración — background task en el startup de la app

- [ ] `src/app.py`
  - `lifespan` (reemplaza el `FastAPI(...)` simple actual por `FastAPI(title=..., lifespan=lifespan)`) que:
    - al arrancar: `asyncio.create_task` de un loop `while True: abrir sesión propia (SessionLocal) → build_verificar_vencimientos_use_case → execute() → cerrar sesión ; await asyncio.sleep(settings.verificador_vencimientos_cadencia_segundos)`, con `try/except` alrededor de `execute()` para que una corrida fallida (ej. error transitorio de BD) no mate el loop
    - al apagar: cancela la tarea (`task.cancel()`) para que los tests que levantan la app con `TestClient`/`httpx.AsyncClient` no queden con un loop colgado
  - Necesario para no romper la suite existente que instancia `app` en tests — validar en Fase 5 que el loop no interfiere con `httpx.ASGITransport`

## Progreso de Implementación

Tareas completadas: 7/7 (100%)

- [x] 1. `EvaluacionActivaQueryPort` (10 min)
- [x] 2. Extender `SuspenderEvaluacionUseCase`/`FinalizarEvaluacionUseCase` con `actor` (20 min)
- [x] 3. `VerificarVencimientosUseCase` (25 min)
- [x] 4. `SQLAlchemyEvaluacionActivaQueryRepository` (25 min)
- [x] 5. Settings (5 min)
- [x] 6. `build_verificar_vencimientos_use_case` factory (10 min)
- [x] 7. Background task en `src/app.py` (20 min)

Verificado: suite de `tests/unit/inc3/` e `tests/integration/inc3/` de `US-3.2.2`/`US-3.2.3`
(36 + 56 tests) sigue en verde tras la extensión de los Use Case existentes. `ASGITransport`
(usado por todos los tests de integración) no dispara el `lifespan` de FastAPI — cero
interferencia entre el background task nuevo y la suite existente.

## Revisión de código obsoleto

No se detectó código obsoleto tras la implementación — todos los archivos nuevos son
componentes nuevos, y los dos Use Case existentes se extendieron sin eliminar ningún camino
de código (el comportamiento por defecto, `actor="estudiante"`, es idéntico al de antes).

## Notas de secuencia

1. Entities/Ports (1) antes que Frameworks (4) — el port es el contrato.
2. Extensión de los Use Case existentes (2) antes de escribir `VerificarVencimientosUseCase` (3) — la Policy los consume tal como quedan extendidos.
3. Settings (5) puede ir en paralelo con 1-3.
4. Dependencies (6) e integración en `app.py` (7) al final — dependen de todo lo anterior.

**Estado:** 0/7 tareas completadas
