# Plan de Implementación: US-6.1.3 - Estudiante se une a una sesión en vivo

**Patrón:** clean-architecture (entities → use_cases → interface_adapters → frameworks, BC-first)
**Producto:** cognion — BC `actividad_evaluativa`

## Decisiones de diseño (a confirmar en este checkpoint)

1. **`participantes_por_sesion` = query de lectura sobre `events`, no tabla propia.** La spec
   deja esta decisión a Fase 2 ("tabla nueva o proyección sobre `events`"). Se toma el mismo
   criterio de `US-3.2.4` (`EvaluacionActivaQueryPort`): a 30-60 alumnos no justifica una
   migración ni una proyección que pueda desincronizarse, y al leer de los propios eventos
   `EstudianteUnido` la consistencia con la escritura es trivial (no hay "misma transacción"
   que garantizar). Reversible si el volumen cambia. La query filtra `aggregate_type =
   'ParticipacionEnVivo'`, `event_type = 'EstudianteUnido'` y `payload->>'sesion_id'`.
2. **`ParticipacionEnVivo` con `id` determinístico** (`uuid5` de `sesion_id:estudiante_id`,
   namespace propio), igual que `Evaluacion.id_para`. Es lo que da la idempotencia (INV-AEV-06):
   dos uniones del mismo par resuelven al mismo stream. Ante `ConcurrenciaOptimistaError` en el
   `append` (dos uniones simultáneas) se relee y se devuelve la existente, como
   `IniciarEvaluacionUseCase` (`US-ADJ-11`).
3. **`ActividadEvaluativaEnVivo.reconstruir()` se implementa ahora** (diferido desde
   `US-6.1.2`): necesitamos saber si la sesión está `Finalizada`. Aplica por `event_type`:
   `SesionEnVivoCreada` arma la base; `SesionEnVivoIniciada` → `EnCurso`;
   `SesionEnVivoFinalizada` → `Finalizada`. **Solo `estado`**: no se inventan payloads de esos
   dos eventos (los define `US-6.1.4` y la Iteración 2); los demás `event_type` se ignoran hasta
   que existan. `US-6.1.4` completa el resto.
4. **Cómo se prueban `EnCurso` y `Finalizada`** (ninguna US previa puede producirlos por API):
   los tests **siembran directamente** un evento `SesionEnVivoIniciada`/`SesionEnVivoFinalizada`
   en el stream de la sesión vía `EventStorePort` (unit: `FakeEventStore`; integración/BDD:
   `SQLAlchemyEventStore`), después de crearla con `POST /sesiones-en-vivo`. Payload mínimo
   (`sesion_id`, `ocurrido_en`). Queda documentado en los tests; cuando `US-6.1.4` exista, el
   `Iniciada` real se podrá usar en lugar de la siembra.
5. **Mensaje de broadcast** (`CanalTiempoRealPort.publicar`, se publica también en el caso
   idempotente, según la spec):
   `{"tipo": "participantes_actualizados", "cantidad": N, "participantes": [{"estudiante_id",
   "unido_en"}]}`. Solo ids, sin nombres: Actividad Evaluativa no tiene puerto a Identidad para
   nombres y agregarlo es alcance de frontend. El canal es best-effort (nunca lanza), así que
   una falla de broadcast no revierte la unión.
6. **Orden de validación:** `EstudianteNoExiste` → `SesionNoExiste` → `SesionYaFinalizada`.
   Aplica también a un estudiante ya unido (sesión finalizada rechaza igual).
7. **Endpoint:** `POST /sesiones-en-vivo/{sesion_id}/unirse`, rol `estudiante`, sin body,
   `estudiante_id` sale del JWT. **200** siempre (creada o idempotente). Errores:
   `SesionNoExiste`/`EstudianteNoExiste` → 404, `SesionYaFinalizada` → 422 (mismo mapeo de
   `EstudianteNoExiste` que `evaluaciones_router`).
8. **Controller:** se **extiende `SesionesEnVivoController`** (pasa a 2 use cases; sus imports
   son 4, muy por debajo del umbral de CBO). No hace falta uno nuevo.
9. **CBO del use case:** 4 puertos (`EstudianteConsultaPort`, `EventStorePort`,
   `ParticipantesSesionQueryPort`, `CanalTiempoRealPort`) + 2 aggregates + errores; el armado
   del mensaje va en una función de módulo para no sumar dependencias. Se verifica en pre-push.

## Componentes a Implementar

### 1. Entities
- [x] `src/actividad_evaluativa/entities/errors.py`
  - `SesionNoExiste(sesion_id)`, `SesionYaFinalizada(sesion_id)`
- [x] `src/actividad_evaluativa/entities/eventos_en_vivo.py`
  - `EstudianteUnido` (`sesion_id`, `estudiante_id`, `unido_en`)
- [x] `src/actividad_evaluativa/entities/participacion_en_vivo.py`
  - `ParticipacionEnVivo` (`id`, `sesion_id`, `estudiante_id`, `unido_en`, `respuestas` vacía)
  - `id_para(sesion_id, estudiante_id)`, `unirse(...)`, `reconstruir(eventos)`
- [x] `src/actividad_evaluativa/entities/actividad_evaluativa_en_vivo.py`
  - `reconstruir(eventos)` + `_aplicar_evento` (`Creada`/`Iniciada`/`Finalizada` → solo `estado`)

### 2. Puerto de lectura
- [x] `src/actividad_evaluativa/entities/ports/participantes_sesion_query_port.py`
  - `ParticipanteResumen(estudiante_id, unido_en)`; `ParticipantesSesionQueryPort.listar(sesion_id)`

### 3. Use Case
- [x] `src/actividad_evaluativa/use_cases/unirse_a_sesion_en_vivo.py`
  - `UnirseASesionEnVivoUseCase.execute(sesion_id, estudiante_id)` → `ParticipacionEnVivo`
  - valida, `append` o reutiliza, lista participantes, publica por `CanalTiempoRealPort`

### 4. Interface Adapter
- [x] `src/actividad_evaluativa/interface_adapters/controllers/sesiones_en_vivo_controller.py`
  - método `unirse(sesion_id, estudiante_id)`

### 5. Frameworks
- [x] `src/actividad_evaluativa/frameworks/adapters/participantes_sesion_query_repository.py`
  - `SQLAlchemyParticipantesSesionQueryRepository` (query sobre `events`, JSONB)
- [x] `src/actividad_evaluativa/frameworks/api/schemas.py`
  - `ParticipacionEnVivoResponse` (`sesion_id`, `estudiante_id`, `unido_en`)
- [x] `src/actividad_evaluativa/frameworks/api/sesiones_en_vivo_router.py`
  - `POST /{sesion_id}/unirse` (rol `estudiante`), mapeo de errores
- [x] `src/actividad_evaluativa/frameworks/dependencies.py`
  - wiring del segundo use case en `get_sesiones_en_vivo_controller`

### 6. Integración
- [x] `src/app.py` sin cambios (el router ya está incluido). Sin migración de DB.

## Tests (Fases 4–6, no forman parte de las tareas de Fase 3)
- Unit: `ParticipacionEnVivo`, `reconstruir` de la sesión, use case (Fakes nuevos:
  `FakeCanalTiempoReal`, `FakeParticipantesSesionQueryPort` que lee del `FakeEventStore`),
  controller.
- Integración: `test_sesiones_en_vivo_unirse_router.py` (HTTP + broadcast por WebSocket real con
  `TestClient`), y del adapter SQL del read model contra la DB real.
- BDD: `tests/step_defs/inc6/test_us_6_1_3_steps.py` sobre
  `tests/features/inc6/US-6.1.3-unirse-sesion-en-vivo.feature`.

**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-09-19
**Tareas:** 12/12 completadas (código: 2 tareas de Fase 3 que agrupan las 12 del checklist)

## Métricas de Tiempo

Tiempos reales medidos por el tracker (PRIN-001: no se comparan contra estimaciones humanas).

| Fase | Real |
|------|------|
| 0 Contexto | 30 s |
| 1 BDD | 24 s |
| 2 Plan | 8 min 37 s (incluye la espera de la aprobación del plan) |
| 3 Implementación | 1 min 4 s |
| 4 Tests unitarios | 2 min 7 s |
| 5 Tests de integración | 42 s |
| 6 Validación BDD | 20 s |
| 7 Quality gates | 8 min 50 s (7 min 5 s solo la suite completa con cobertura) |
| 8 Documentación | ver reporte final (`docs/reports/inc6/US-6.1.3-report.md`) |

## Desvíos respecto del plan

- Ninguno de diseño: las 9 decisiones se implementaron como se aprobaron.
- Fuera del checklist: actualizar el test unitario del controller de `US-6.1.2`
  (`test_crear_sesion_en_vivo_use_case.py`), que construía `SesionesEnVivoController` con un
  solo use case y se rompió al agregar el segundo; y `tests/integration/inc6/_helpers.py`
  (nuevo) para compartir la preparación de sesión/estudiante entre integración y BDD.

## Lecciones Aprendidas

- ✅ Aplicar la lección de `US-6.1.2` (suite completa primero, `codeguard` después y en serie)
  dio un cierre limpio: 1286 passed sin errores y CodeGuard sin timeouts de herramienta.
- ✅ Leer la spec como "a decidir en Fase 2" y elegir la variante barata (query sobre `events`
  en vez de tabla propia, criterio de `US-3.2.4`) evitó una migración y una proyección que
  pudiera desincronizarse.
- ✅ Diferir `reconstruir()` en `US-6.1.2` fue correcto: recién acá hay un consumidor, y quedó
  acotado a lo que hace falta (`estado`) sin inventar payloads de eventos que no existen aún.
- ⚠️ Agregar un segundo use case al constructor de un controller rompe los tests de la US
  anterior que lo construyen. Conviene grepear los `Controller(` de los tests antes de tocar
  una firma.
- 💡 Los estados que ninguna US produce todavía (`EnCurso`, `Finalizada`) se prueban sembrando
  el evento en el event store; cuando `US-6.1.4` exista, el `Iniciada` real reemplaza la
  siembra en los tests.
- 💡 `TestClient` sincrónico + `asyncio.run` para preparar datos permite verificar el broadcast
  real por WebSocket junto a un request HTTP, sin fixtures async especiales (`NullPool`).
