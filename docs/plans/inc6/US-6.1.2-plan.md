# Plan de Implementación: US-6.1.2 - Docente crea una sesión en vivo desde el detalle de una Comisión

**Patrón:** clean-architecture (entities → use_cases → interface_adapters → frameworks, BC-first)
**Producto:** cognion — BC `actividad_evaluativa`

## Decisiones de diseño (a confirmar en este checkpoint)

1. **Un solo acceso al banco, no dos.** A diferencia de `CrearActividadPeriodoAbierto`
   (`contar_activas_por_materia` y luego nada más), acá el set se sampleá al crear, así que el
   Use Case llama solo a `listar_ids_activas_por_materia` y valida INV-AEV-01 con `len(ids)`.
   Evita una segunda query idéntica sin cambiar la semántica (mismo error `PreguntasInsuficientes`).
2. **Sin `MateriaConsultaPort`.** El Use Case necesita `materia_id` (lo da `ComisionConsultaPort`,
   `US-6.1.1`) pero no el nombre de la materia — no hay notificación en esta US. Dependencias del
   Use Case: `ComisionConsultaPort`, `PreguntaConsultaPort`, `EventStorePort` (3, sin riesgo de
   CBO).
3. **Controller nuevo y separado** (`SesionesEnVivoController`), no se toca
   `ActividadesController` (ya 4 use cases inyectados, mismo criterio que `BancosController` en
   `US-2.1.7`).
4. **INV-AEV-02 (tiempo > 0) vive en el aggregate** (`ActividadEvaluativaEnVivo.crear`), igual que
   INV-AE-02/03 en `ActividadEvaluativaPeriodoAbierto.crear`. INV-AEV-01 vive en el Use Case
   (requiere el puerto).
5. **Orden de validación en el Use Case:** `ComisionNoExiste` → `PreguntasInsuficientes` →
   `TiempoLimiteInvalido` (este último lo levanta `crear`, después del sampleo).
6. **`aggregate_type = "ActividadEvaluativaEnVivo"`**, `expected_sequence_number=0`, un solo
   evento `SesionEnVivoCreada`. `reconstruir()` NO se implementa en esta US (nadie lo consume
   todavía; lo agrega `US-6.1.3`/`US-6.1.4` cuando necesiten leer la sesión) — evita código sin
   caller.
7. **Respuesta HTTP 201** con resumen sin las preguntas (`id`, `comision_id`, `materia_id`,
   `unidad_tematica`, `tema`, `cantidad_preguntas`, `tiempo_limite_por_pregunta_segundos`,
   `estado`), según la postcondición de la spec.
8. **Errores HTTP:** `ComisionNoExiste` → 404; `PreguntasInsuficientes`/`TiempoLimiteInvalido` →
   422. `cantidad_preguntas` ≥ 1 se valida en el schema (`Field(ge=1)`), igual que
   `CrearActividadRequest`. `tiempo_limite_por_pregunta_segundos` **no** lleva `gt=0` en el schema
   — si lo tuviera, el 422 de Pydantic taparía `TiempoLimiteInvalido` y la invariante de dominio
   nunca se ejercitaría desde HTTP (el escenario BDD pide ese error de dominio).

## Componentes a Implementar

### 1. Entities
- [x] `src/actividad_evaluativa/entities/errors.py`
  - `ComisionNoExiste(comision_id)`, `TiempoLimiteInvalido(tiempo_limite_segundos)`
- [x] `src/actividad_evaluativa/entities/actividad_evaluativa_en_vivo.py`
  - `EstadoSesionEnVivo` (`EN_ESPERA`/`EN_CURSO`/`FINALIZADA`)
  - `ActividadEvaluativaEnVivo` (dataclass, atributos de §14) + `crear(...)` → estado
    `EN_ESPERA`, `pregunta_actual_indice=None`, `opciones_mostradas=False`,
    `pregunta_actual_cerrada=False`; valida INV-AEV-02
  - Reutiliza `PreguntaAsignada` y `Evaluacion.armar_preguntas_asignadas` (VO ya existentes)
- [x] `src/actividad_evaluativa/entities/eventos_en_vivo.py`
  - `SesionEnVivoCreada` (dataclass frozen) + `desde_sesion(...)`

### 2. Use Case
- [x] `src/actividad_evaluativa/use_cases/crear_sesion_en_vivo.py`
  - `CrearSesionEnVivoUseCase.execute(comision_id, cantidad_preguntas,
    tiempo_limite_por_pregunta_segundos, unidad_tematica=None, tema=None)` → aggregate
  - Resuelve `materia_id`, samplea con `random.sample`, construye aggregate, `append` del
    primer evento

### 3. Interface Adapter
- [x] `src/actividad_evaluativa/interface_adapters/controllers/sesiones_en_vivo_controller.py`
  - `SesionesEnVivoController.crear(...)` → delega en el Use Case

### 4. Frameworks
- [x] `src/actividad_evaluativa/frameworks/api/schemas.py`
  - `CrearSesionEnVivoRequest`, `SesionEnVivoResponse`
- [x] `src/actividad_evaluativa/frameworks/api/sesiones_en_vivo_router.py`
  - `POST /sesiones-en-vivo` (rol `docente`), mapeo de errores
- [x] `src/actividad_evaluativa/frameworks/dependencies.py`
  - `get_sesiones_en_vivo_controller(session)`; `SesionesEnVivoController` no necesita
    `require_*` nuevo (`require_docente` ya existe)

### 5. Integración
- [x] `src/app.py` ya incluye `sesiones_en_vivo_router` (`US-6.1.1`) — sin cambios.
- [x] Sin migración de DB: `events` ya admite cualquier `aggregate_type` (`US-3.1.1`).

## Tests (Fases 4–6, no forman parte de las tareas de Fase 3)
- Unit: aggregate, evento, Use Case (con Fakes de `tests/unit/inc3/_fakes.py` + Fake nuevo de
  `ComisionConsultaPort`), controller.
- Integration: `tests/integration/inc6/test_sesiones_en_vivo_router.py`.
- BDD: `tests/step_defs/inc6/test_us_6_1_2_steps.py` sobre
  `tests/features/inc6/US-6.1.2-crear-sesion-en-vivo.feature`.

**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-09-18
**Tareas:** 9/9 completadas (código: 3 tareas de Fase 3 que agrupan las 9 del checklist)

## Métricas de Tiempo

Tiempos reales medidos por el tracker (PRIN-001: no se comparan contra estimaciones humanas).

| Fase | Real |
|------|------|
| 0 Contexto | 29 s |
| 1 BDD | 25 s |
| 2 Plan | 1 min 20 s |
| 3 Implementación | 1 min 26 s |
| 4 Tests unitarios | 53 s |
| 5 Tests de integración | 1 min 24 s |
| 6 Validación BDD | 54 s |
| 7 Quality gates | 20 min 24 s (16 min 23 s solo la suite completa con cobertura) |
| 8 Documentación | ver reporte final (`docs/reports/inc6/US-6.1.2-report.md`) |

## Lecciones Aprendidas

- ✅ Un solo `listar_ids_activas_por_materia` alcanza para validar INV-AEV-01 y sortear el set
  — no hace falta `contar_activas_por_materia` aparte cuando el sampleo ocurre al crear.
- ✅ Controller separado desde el diseño (Fase 2) evitó el CRITICAL de CBO que apareció en
  `US-2.1.2`/`2.1.5`/`2.1.6`.
- ⚠️ `tests/integration/inc6/` sin `conftest.py` propio dejó preguntas huérfanas que rompieron
  20 tests de `step_defs/inc1`/`inc2` recién en la corrida completa (FK en `DELETE FROM banco`).
  Cada carpeta `tests/integration/incN/` que crea preguntas necesita su `conftest.py` de
  limpieza — corregido con el mismo patrón de `inc5`. Invisible corriendo solo los tests de la US.
- ⚠️ `codeguard` invocado como `.venv/bin/codeguard` no encuentra `vulture`/`codespell` (los
  busca por nombre en `PATH`): 16 checks figuran "not installed" sin que sea un hallazgo de
  código. Correr con `PATH="$PWD/.venv/bin:$PATH"`.
- ⚠️ La suite completa tarda ~16 min y compite por CPU con `codeguard`, que entonces reporta
  timeouts de pylint/mypy — correrlos en serie, no en paralelo.
- 💡 Sin `MateriaConsultaPort` en el Use Case (no se necesita el nombre de la materia): 3
  dependencias en vez de 4, sin riesgo de CBO.
