# Reporte de Implementación: US-6.1.2

## Resumen Ejecutivo

- **Historia de Usuario:** US-6.1.2 — Docente crea una sesión en vivo desde el detalle de una Comisión
- **Puntos estimados:** 3
- **Tiempo real:** ~29 min (tracker; incluye ~16 min de la suite completa con cobertura en Fase 7 — PRIN-001, tiempo real de ejecución del agente, no comparable contra estimación humana)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-09-18

---

## Componentes Implementados

### Entities (`src/actividad_evaluativa/entities/`)

- ✅ **`ActividadEvaluativaEnVivo`** (`actividad_evaluativa_en_vivo.py`) — aggregate raíz del modo en vivo con los atributos de `BC-actividad-evaluativa-modelo.md` §14; `crear(...)` lo construye en `EnEspera` (`pregunta_actual_indice=None`, `opciones_mostradas=False`, `pregunta_actual_cerrada=False`) y valida INV-AEV-02. Incluye `EstadoSesionEnVivo` (`EnEspera`/`EnCurso`/`Finalizada`)
- ✅ **`SesionEnVivoCreada`** (`eventos_en_vivo.py`) — evento de dominio, primer evento del stream; `desde_sesion(...)` mueve la construcción fuera del Use Case (evita CBO, mismo criterio que `ActividadEvaluativaCreada`)
- ✅ **`ComisionNoExiste`, `TiempoLimiteInvalido`** (`errors.py`) — errores de dominio nuevos

### Use Cases (`src/actividad_evaluativa/use_cases/`)

- ✅ **`CrearSesionEnVivoUseCase`** (`crear_sesion_en_vivo.py`) — resuelve `materia_id` vía `ComisionConsultaPort`, valida INV-AEV-01 con `len(ids)` de `listar_ids_activas_por_materia` (una sola consulta al banco), sortea el set con `random.sample`, construye el aggregate y hace `append` del primer evento (`sequence_number=1`)

### Interface Adapters

- ✅ **`SesionesEnVivoController`** (`controllers/sesiones_en_vivo_controller.py`) — controller nuevo y separado de `ActividadesController` (ya con 4 use cases)

### Frameworks (`src/actividad_evaluativa/frameworks/`)

- ✅ **`POST /sesiones-en-vivo`** (`api/sesiones_en_vivo_router.py`, rol `docente`) — 201 con resumen sin preguntas; `ComisionNoExiste` → 404, `PreguntasInsuficientes`/`TiempoLimiteInvalido` → 422
- ✅ **`CrearSesionEnVivoRequest`/`SesionEnVivoResponse`** (`api/schemas.py`)
- ✅ **`get_sesiones_en_vivo_controller`** (`dependencies.py`) — wiring con 3 puertos

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **Pylint** | 9.84/10 | ≥ 8.0 | ✅ |
| **Complejidad Ciclomática (máx/función)** | 5 (promedio 1.5) | ≤ 10 | ✅ |
| **Índice de Mantenibilidad (mín)** | 60.23 (promedio 83.99) | > 20 | ✅ |
| **Coverage (`entities`/`use_cases`/`interface_adapters` del BC)** | 100% | ≥ 95% | ✅ |
| **CodeGuard** (8 archivos analizados) | 4 errors, 201 warnings | 0 CRITICAL | ✅ |

**Estado General:** ✅ APROBADO (`quality/reports/inc6/US-6.1.2-quality.json`)

> `frameworks/` está excluido del gate de coverage por `pyproject.toml` (mismo criterio en
> todos los BCs). El router, `dependencies.py` y `schemas.py` se validan con 8 tests de
> integración contra la app real y 5 escenarios BDD.

### Detalle de CodeGuard

> Generado con `--analysis-type full` y `.venv/bin` en el `PATH`
> (`quality/reports/inc6/US-6.1.2-codeguard.json`).

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 8 |
| PEP8 | 0 | 1 | 7 |
| Complexity | 0 | 0 | 8 |
| DeadCode | 0 | 156 | 0 |
| Maintainability | 0 | 0 | 8 |
| Pylint | 2 | 0 | 6 |
| Spelling | 0 | 44 | 1 |
| Types | 0 | 0 | 8 |
| UnusedImports | 2 | 0 | 6 |

Los 4 errors son timeouts de pylint dentro de CodeGuard (>5s/>10s), no hallazgos de código —
`pylint` corrido directamente da 9.84/10. `DeadCode` y `Spelling` son ruido conocido: el primero
analiza archivo por archivo sin ver usos cross-módulo, el segundo compara texto en español con
un diccionario en inglés. El único warning real de `PEP8` es una línea larga preexistente
(`dependencies.py:54`), no de esta US.

---

## Tests Implementados

### Tests Unitarios (18 tests nuevos, `tests/unit/inc6/`)

- ✅ `test_actividad_evaluativa_en_vivo.py` — aggregate (estado inicial, normalización de
  unidad/tema, INV-AEV-02 con `0` y negativo, ids únicos), `SesionEnVivoCreada.desde_sesion`,
  errores nuevos
- ✅ `test_crear_sesion_en_vivo_use_case.py` — creación y persistencia del primer evento, set
  fijado coincide con el persistido, filtro por unidad/tema, `ComisionNoExiste`,
  `PreguntasInsuficientes` sin persistir nada, borde exacto (pide todas las disponibles),
  `TiempoLimiteInvalido` sin persistir, `SesionesEnVivoController`
- ✅ `_fakes.py` — `FakeComisionConsultaPort`

**Estado:** 30/30 pasando en `tests/unit/inc6/` (18 nuevos + 12 de `US-6.1.1`). Cobertura 100%
de los 4 archivos nuevos de `entities`/`use_cases`/`interface_adapters`.

### Tests de Integración (8 tests, `tests/integration/inc6/test_sesiones_en_vivo_router.py`)

- ✅ Creación exitosa (verifica `sequence_number=1` y el payload en la tabla `events`), filtro
  por unidad/tema, preguntas insuficientes, tiempo límite inválido, comisión inexistente,
  rechazo por rol Estudiante, sin token, `cantidad_preguntas=0` rechazada por schema

**Estado:** 8/8 pasando

### Escenarios BDD (5 escenarios, `tests/features/inc6/US-6.1.2-crear-sesion-en-vivo.feature`)

- ✅ Creación exitosa · preguntas insuficientes · tiempo límite inválido · comisión inexistente
  · rechazo por rol — step defs en `tests/step_defs/inc6/test_us_6_1_2_steps.py`

**Estado:** 5/5 pasando

**Suite completa del proyecto** (`tests/`, sin acotar): 1224 passed, 1 failed, 20 errors en la
primera corrida. El fallo es `tests/step_defs/inc3/test_us_3_2_1_steps.py::test_rechazo_fuera_del_período_vigente`
(preexistente, ventana de ~1s, documentado en `CLAUDE.md`). Los 20 errores eran propios de esta
US (ver "Desafíos"): se corrigieron y se re-ejecutaron los tests afectados (44 passed). **No se
repitió la suite completa** después del fix.

---

## Archivos Creados/Modificados

### Código de Producción

- `src/actividad_evaluativa/entities/actividad_evaluativa_en_vivo.py` (nuevo)
- `src/actividad_evaluativa/entities/eventos_en_vivo.py` (nuevo)
- `src/actividad_evaluativa/entities/errors.py` (modificado — 2 errores nuevos)
- `src/actividad_evaluativa/use_cases/crear_sesion_en_vivo.py` (nuevo)
- `src/actividad_evaluativa/interface_adapters/controllers/sesiones_en_vivo_controller.py` (nuevo)
- `src/actividad_evaluativa/frameworks/api/sesiones_en_vivo_router.py` (modificado — `POST`)
- `src/actividad_evaluativa/frameworks/api/schemas.py` (modificado)
- `src/actividad_evaluativa/frameworks/dependencies.py` (modificado — wiring)

### Tests

- `tests/unit/inc6/_fakes.py`, `test_actividad_evaluativa_en_vivo.py`, `test_crear_sesion_en_vivo_use_case.py` (nuevos)
- `tests/integration/inc6/test_sesiones_en_vivo_router.py`, `conftest.py` (nuevos)
- `tests/features/inc6/US-6.1.2-crear-sesion-en-vivo.feature` (nuevo)
- `tests/step_defs/inc6/__init__.py`, `test_us_6_1_2_steps.py` (nuevos)

### Documentación

- `docs/plans/inc6/US-6.1.2-context.md`, `US-6.1.2-plan.md`
- `docs/specs/inc6/US-6.1.2.md` (estado → `Implementada`)
- `docs/reports/inc6/US-6.1.2-report.md` (este archivo)
- `quality/reports/inc6/US-6.1.2-quality.json`, `-codeguard.json`, `-coverage.json`

---

## Desafíos y Soluciones

### Desafío 1: 20 errores en la suite completa por datos huérfanos

**Descripción:** Corriendo solo los tests de la US todo pasaba, pero la suite completa mostró 20
errores en `tests/step_defs/inc1`/`inc2`: `ForeignKeyViolation` en `DELETE FROM banco`. Mi test
de integración crea preguntas por la API y `tests/integration/inc6/` no tenía `conftest.py` de
limpieza; siendo el último directorio de integración en orden alfabético, dejaba las
preguntas justo antes de los step defs de `inc1`.

**Solución:** `tests/integration/inc6/conftest.py` con el mismo `autouse` de limpieza que
`inc5` (`events`, `pregunta_plantilla`, `banco`, `materia`). Verificado: 44 tests
(`integration/inc6` + `step_defs/inc1` + los dos de `inc2` afectados) pasan y la tabla
`pregunta_plantilla` queda en 0.

### Desafío 2: Que la invariante de dominio se ejercite desde HTTP

**Descripción:** Si `tiempo_limite_por_pregunta_segundos` llevara `gt=0` en el schema Pydantic,
el 422 genérico taparía `TiempoLimiteInvalido` y INV-AEV-02 nunca se ejercitaría por la API.

**Solución:** El schema solo exige `cantidad_preguntas >= 1`; el tiempo lo valida el aggregate.
Documentado en el docstring de `CrearSesionEnVivoRequest`.

### Desafío 3: CodeGuard con timeouts y checks "not installed"

**Descripción:** Corrido en paralelo a la suite completa, `codeguard` reportó timeouts de
pylint/mypy; y sin `.venv/bin` en el `PATH`, `DeadCode`/`Spelling` figuraban "not installed"
(mismo hallazgo ya anotado en el reporte de `US-6.1.1`).

**Solución:** Correr `codeguard` en serie (con la máquina libre) y con
`PATH="$PWD/.venv/bin:$PATH"`. Quedan 4 timeouts de pylint dentro de la herramienta; el score
se midió directo.

---

## Cambios no Previstos

- Se agregó `tests/integration/inc6/conftest.py` (no estaba en el plan) — ver Desafío 1.
- `reconstruir()` del aggregate **no** se implementó (decisión de Fase 2): nadie lo consume
  hasta `US-6.1.3`/`US-6.1.4`.

---

## Criterios de Aceptación

- [x] Creación exitosa: sesión en `EnEspera` con las preguntas fijadas al azar, HTTP 201 con el `sesion_id`
- [x] Preguntas insuficientes → `PreguntasInsuficientes` (422), no se crea ninguna sesión
- [x] Tiempo límite inválido → `TiempoLimiteInvalido` (422)
- [x] Comisión inexistente → `ComisionNoExiste` (404)
- [x] Rechazo por rol Estudiante → 403

**Estado:** 5/5 cumplidos

---

## Próximos Pasos

- [ ] `US-6.1.3` — Estudiante se une a la sesión (necesitará `reconstruir()` del aggregate)
- [ ] `US-6.1.4` — Docente inicia la sesión (primer broadcast real de un evento de dominio)
- [ ] Frontend: entry point "+ Nueva sesión en vivo" desde `ComisionDetalleDocente.tsx`, todavía sin iteración asignada en `inc6-candidatas.md`

---

## Lecciones Aprendidas

- ✅ Un solo `listar_ids_activas_por_materia` alcanza para validar INV-AEV-01 y sortear el set.
- ✅ Diseñar el controller separado en Fase 2 evitó el CRITICAL de CBO que apareció en
  `US-2.1.2`/`2.1.5`/`2.1.6`.
- ⚠️ Cada `tests/integration/incN/` que crea preguntas necesita su `conftest.py` de limpieza —
  el problema solo aparece en la corrida completa, nunca acotando a los tests de la US.
- ⚠️ No correr `codeguard` en paralelo a la suite completa, y hacerlo con `.venv/bin` en el `PATH`.
- ⚠️ Confirmar con la suite completa antes de dar por buena la Fase 7: la primera corrida ya
  mostraba los 20 errores.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-09-18
