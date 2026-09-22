# Plan de Implementación: US-6.3.2 - Listar las sesiones en vivo de una Comisión

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** Cognion — BC Actividad Evaluativa

## Decisión de diseño (Fase 2)

- **Sin proyección sincronizada**, mismo criterio que `EvaluacionActivaQueryPort` (`US-3.2.4`):
  el adapter lee la tabla `events` completa del `aggregate_type = "ActividadEvaluativaEnVivo"`,
  agrupa por `aggregate_id` y deriva `comision_id`/`materia_id`/`estado`/`creada_en` del primer
  y del último evento de cada stream — sin migración nueva.
- **Resolución de rol en el use case, no en el router**: `ListarSesionesEnVivoUseCase` recibe
  `usuario_id`, `rol` y `comision_id` (opcional, tal como llega del query param) y decide la
  Comisión efectiva — Estudiante: la propia (`EstudianteConsultaPort.obtener_comision_id`, ya
  existente), rechazando si pide otra (`ComisionNoAutorizada`, 403); Docente: la que pasa,
  obligatoria (`ComisionRequerida`, 422 si falta). Dos excepciones nuevas en `errors.py`.
- **`materia_nombre` resuelto con `MateriaConsultaPort` ya existente** (mismo criterio que
  `US-6.3.1` con nombres de Estudiantes): el read model local (`SesionEnVivoResumen`) no conoce
  Materia, el use case lo completa con `dataclasses.replace()` por cada `materia_id` único del
  resultado (normalmente 1, ya que todas las sesiones de una Comisión comparten Materia).
- **Sin dependencia nueva en `SesionesEnVivoQueryController`** más allá del 4° use case — ya
  tiene 3 (`US-6.2.8`); si el pre-push marca CRITICAL de CBO, se separa en un controller propio
  (mismo patrón que `BancosController`/`US-2.1.7`), decisión a confirmar recién si ocurre.

## Componentes a Implementar

### 1. Entities

- [x] `src/actividad_evaluativa/entities/errors.py`
  - `ComisionRequerida` (Docente sin `comision_id`, 422)
  - `ComisionNoAutorizada` (Estudiante pidiendo la Comisión de otro, 403)
- [x] `src/actividad_evaluativa/entities/ports/sesiones_en_vivo_query_port.py` (nuevo)
  - `SesionEnVivoResumen` (frozen dataclass): `id, comision_id, materia_id, materia_nombre: str = "", cantidad_preguntas, tiempo_limite_por_pregunta_segundos, estado: EstadoSesionEnVivo, unidad_tematica, tema, creada_en`
  - `SesionesEnVivoQueryPort.listar(comision_id, estados: list[EstadoSesionEnVivo]) -> list[SesionEnVivoResumen]` — más recientes primero

### 2. Use Cases

- [x] `src/actividad_evaluativa/use_cases/listar_sesiones_en_vivo.py` (nuevo)
  - `ListarSesionesEnVivoUseCase(estudiante_consulta, sesiones_query, materia_consulta)`
  - `execute(usuario_id, rol, comision_id, estados) -> list[SesionEnVivoResumen]`

### 3. Interface Adapters

- [x] `src/actividad_evaluativa/interface_adapters/controllers/sesiones_en_vivo_query_controller.py`
  - Método `listar_sesiones(usuario_id, rol, comision_id, estados)`, 4° use case inyectado

### 4. Frameworks

- [x] `src/actividad_evaluativa/frameworks/adapters/sesiones_en_vivo_query_repository.py` (nuevo)
  - `SQLAlchemySesionesEnVivoQueryRepository` — agrupa `events` en memoria (`groupby`, mismo
    patrón que `evaluacion_activa_query_repository.py`), filtra por `comision_id` y por
    `estados`, ordena por `creada_en` descendente
- [x] `src/actividad_evaluativa/frameworks/api/schemas.py`
  - `SesionEnVivoResumenResponse`
- [x] `src/actividad_evaluativa/frameworks/api/sesiones_en_vivo_router.py`
  - `GET /sesiones-en-vivo` (sin `{sesion_id}`, no colisiona), `require_estudiante_o_docente`,
    query params `comision_id: UUID | None`, `estado: list[str]` (default `["EnEspera", "EnCurso"]`) →
    404 no aplica; 422/403 desde las excepciones nuevas
- [x] `src/actividad_evaluativa/frameworks/dependencies.py`
  - `get_sesiones_en_vivo_query_controller` gana `ListarSesionesEnVivoUseCase` con
    `EstudianteConsultaPortInProcess`, `SQLAlchemySesionesEnVivoQueryRepository`,
    `MateriaConsultaPortInProcess` (ya usado en otros use cases del BC)

### 5. Integración

- [x] `tests/unit/inc6/_fakes.py` o `tests/unit/inc3/_fakes.py` — `FakeSesionesEnVivoQueryPort`
  nuevo y/o extender `FakeMateriaConsultaPort` si falta
- [x] `tests/unit/inc6/`, `tests/integration/inc6/`, `tests/features/inc6/US-6.3.2*.feature` + step defs

**Estado:** 9/9 tareas completadas ✅

**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-09-22

## Métricas de Tiempo

- **Tiempo real (tracker):** ~23 min hasta el cierre de Fase 7 (Fases 0 a 7)

## Lecciones aprendidas

- ✅ El precedente de `EvaluacionActivaQueryPort`/`SQLAlchemyEvaluacionActivaQueryRepository`
  (`US-3.2.4`) se trasladó directo: agrupar `events` en memoria sin proyección, misma función
  de módulo `_resumen_de_stream` testeable sin sesión de BD.
- ✅ El fake de `SesionesEnVivoQueryPort` derivando del `FakeEventStore._streams` (mismo patrón
  que `FakeParticipantesSesionQueryPort`) permitió testear el controller sin duplicar lógica de
  agrupamiento en el test.
- 💡 Para probar "dos sesiones en la misma Comisión" u "orden por recientes" hizo falta un
  helper nuevo (`_crear_sesion`, POST directo reutilizando el banco de preguntas de
  `preparar_sesion`) — el helper existente siempre crea una Comisión nueva por sesión.
- 💡 También hizo falta un helper para "Comisión sin sesiones" (`_crear_comision_sin_sesion`):
  `preparar_sesion()` siempre crea una sesión, así que no servía para el caso vacío.
- ⚠️ `SesionesEnVivoQueryController` con 4 use cases inyectados sí marcó CRITICAL de CBO
  (11/10) recién en el pre-push (no en Fase 7, que no mide CBO) — exactamente el riesgo que
  pedía vigilar la spec. Se resolvió separando `listar_sesiones` en
  `SesionesEnVivoListadoController` propio, mismo patrón que `BancosController` (`US-2.1.7`).
