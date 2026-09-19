# Reporte de Implementación: US-6.1.3

## Resumen Ejecutivo

- **Historia de Usuario:** US-6.1.3 — Estudiante se une a una sesión en vivo
- **Puntos estimados:** 3
- **Tiempo real:** ~24 min (tracker; incluye ~7 min de la suite completa con cobertura en Fase 7 y ~8,5 min de espera de la aprobación del plan en Fase 2 — PRIN-001, tiempo real de ejecución del agente, no comparable contra estimación humana)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-09-19

---

## Componentes Implementados

### Entities (`src/actividad_evaluativa/entities/`)

- ✅ **`ParticipacionEnVivo`** (`participacion_en_vivo.py`) — segundo aggregate del modo en vivo; `id` determinístico por `uuid5(sesion_id:estudiante_id)` (`id_para`), que sostiene INV-AEV-06; `unirse(...)` y `reconstruir(eventos)`. `respuestas` queda vacía (las agrega la Iteración 2)
- ✅ **`EstudianteUnido`** (`eventos_en_vivo.py`) — evento de dominio, primer evento del stream de la participación; `desde_participacion(...)`
- ✅ **`ActividadEvaluativaEnVivo.reconstruir()`** (`actividad_evaluativa_en_vivo.py`) — diferido desde `US-6.1.2`; replay por `event_type`, hoy solo mueve `estado` (`SesionEnVivoIniciada` → `EnCurso`, `SesionEnVivoFinalizada` → `Finalizada`). `validar_para_unirse()` rechaza solo `Finalizada`
- ✅ **`SesionNoExiste`, `SesionYaFinalizada`** (`errors.py`) — errores de dominio nuevos
- ✅ **`ParticipantesSesionQueryPort`** (`ports/participantes_sesion_query_port.py`) — puerto de lectura del read model `participantes_por_sesion`, con `ParticipanteResumen`

### Use Cases (`src/actividad_evaluativa/use_cases/`)

- ✅ **`UnirseASesionEnVivoUseCase`** (`unirse_a_sesion_en_vivo.py`) — valida estudiante, sesión y estado; crea la participación o reutiliza la existente (idempotente, con recuperación ante `ConcurrenciaOptimistaError`); publica por `CanalTiempoRealPort` la lista de participantes actualizada, también en el caso idempotente

### Interface Adapters

- ✅ **`SesionesEnVivoController.unirse(...)`** — el controller pasa a inyectar 2 use cases (sigue muy por debajo del umbral de CBO)

### Frameworks (`src/actividad_evaluativa/frameworks/`)

- ✅ **`POST /sesiones-en-vivo/{sesion_id}/unirse`** (`api/sesiones_en_vivo_router.py`, rol `estudiante`) — 200 siempre (creada o idempotente); `SesionNoExiste`/`EstudianteNoExiste` → 404, `SesionYaFinalizada` → 422
- ✅ **`SQLAlchemyParticipantesSesionQueryRepository`** (`adapters/participantes_sesion_query_repository.py`) — deriva `participantes_por_sesion` de los eventos `EstudianteUnido` de `events` (filtro JSONB por `sesion_id`), sin tabla propia
- ✅ **`ParticipacionEnVivoResponse`** (`api/schemas.py`) y wiring en `dependencies.py`

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **Pylint** | 9.83/10 | ≥ 8.0 | ✅ |
| **Complejidad Ciclomática (máx/función)** | 5 (promedio 1.55) | ≤ 10 | ✅ |
| **Índice de Mantenibilidad (mín)** | 59.69 (promedio 85.34) | > 20 | ✅ |
| **Coverage (`entities`/`use_cases`/`interface_adapters` del BC)** | 100% | ≥ 95% | ✅ |
| **CodeGuard** (11 archivos analizados) | 1 error, 218 warnings | 0 CRITICAL | ✅ |

**Estado General:** ✅ APROBADO (`quality/reports/inc6/US-6.1.3-quality.json`)

> `frameworks/` está excluido del gate de coverage por `pyproject.toml` (mismo criterio en
> todos los BCs). El adapter SQL y el router se validan con 24 tests de integración contra la
> DB real y con BDD.

### Detalle de CodeGuard

> Generado con `--analysis-type full` y `.venv/bin` en el `PATH`, en serie y con la máquina
> libre (`quality/reports/inc6/US-6.1.3-codeguard.json`).

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 11 |
| PEP8 | 0 | 1 | 10 |
| Complexity | 0 | 0 | 11 |
| DeadCode | 1 | 171 | 0 |
| Maintainability | 0 | 0 | 11 |
| Pylint | 0 | 0 | 11 |
| Spelling | 0 | 46 | 3 |
| Types | 0 | 0 | 11 |
| UnusedImports | 0 | 0 | 11 |

El único error es un falso positivo de `DeadCode` (100% de confianza) sobre el parámetro
`sesion_id` de un método abstracto de `ParticipantesSesionQueryPort` — el mismo patrón ya
aceptado en todos los puertos ABC del proyecto (`US-6.1.1`). `DeadCode` (171) y `Spelling` (46)
son ruido conocido: el primero analiza archivo por archivo sin ver usos cross-módulo, el segundo
compara texto en español con un diccionario en inglés. El único warning de `PEP8` es un import
preexistente (`dependencies.py:57`).

---

## Tests Implementados

### Tests Unitarios (25 tests nuevos, `tests/unit/inc6/`)

- ✅ `test_participacion_en_vivo.py` — `id_para` (determinístico, distingue sesión/estudiante,
  no colisiona con el par invertido), `unirse`, `reconstruir`, `EstudianteUnido`, errores
- ✅ `test_actividad_evaluativa_en_vivo.py` (ampliado) — `reconstruir` de la sesión (creada,
  `Iniciada`, `Finalizada`, `event_type` sin efecto) y `validar_para_unirse`
- ✅ `test_unirse_a_sesion_en_vivo_use_case.py` — unión en espera y tardía (`EnCurso`),
  acumulación de participantes en el broadcast, idempotencia (sin segundo evento, también
  publica), carrera concurrente al insertar, y rechazos (sesión inexistente, finalizada sin
  persistir ni publicar, ya unido con sesión terminada, estudiante inexistente); controller
- ✅ `_fakes.py` (ampliado) — `FakeCanalTiempoReal`, `FakeParticipantesSesionQueryPort`

**Estado:** 55/55 pasando en `tests/unit/inc6/` (25 nuevos). Cobertura 100% de todos los
archivos nuevos de `entities`/`use_cases`/`interface_adapters`.

### Tests de Integración (11 tests nuevos, `tests/integration/inc6/`)

- ✅ `test_sesiones_en_vivo_unirse_router.py` — unión en espera, tardía, idempotente, sesión
  finalizada (422), inexistente (404), estudiante que no existe en Identidad (404), rol docente
  (403), sin token; adapter del read model (orden de unión y aislamiento entre sesiones, lista
  vacía); y **broadcast real por WebSocket**: un Docente conectado recibe la lista cuando se une
  un alumno
- ✅ `_helpers.py` (nuevo) — preparación de sesión/estudiante y siembra de eventos, compartido
  con BDD

**Estado:** 24/24 pasando en `tests/integration/inc6/` (11 nuevos)

### Escenarios BDD (5 escenarios nuevos, `tests/features/inc6/US-6.1.3-unirse-sesion-en-vivo.feature`)

- ✅ Unión en espera (con broadcast al Docente) · unión tardía · unión idempotente · sesión
  finalizada · sesión inexistente — step defs en `tests/step_defs/inc6/test_us_6_1_3_steps.py`

**Estado:** 10/10 pasando en `tests/step_defs/inc6/` (5 nuevos)

**Suite completa del proyecto** (`tests/`, sin acotar, corrida antes de `codeguard`): **1286
passed, 0 failed, 0 errors** en 7 min 5 s, incluido el test flaky preexistente de `US-3.2.1`.

---

## Archivos Creados/Modificados

### Código de Producción

- `src/actividad_evaluativa/entities/participacion_en_vivo.py` (nuevo)
- `src/actividad_evaluativa/entities/ports/participantes_sesion_query_port.py` (nuevo)
- `src/actividad_evaluativa/use_cases/unirse_a_sesion_en_vivo.py` (nuevo)
- `src/actividad_evaluativa/frameworks/adapters/participantes_sesion_query_repository.py` (nuevo)
- `src/actividad_evaluativa/entities/actividad_evaluativa_en_vivo.py` (modificado — `reconstruir`, `validar_para_unirse`)
- `src/actividad_evaluativa/entities/eventos_en_vivo.py` (modificado — `EstudianteUnido`)
- `src/actividad_evaluativa/entities/errors.py` (modificado — 2 errores nuevos)
- `src/actividad_evaluativa/interface_adapters/controllers/sesiones_en_vivo_controller.py` (modificado)
- `src/actividad_evaluativa/frameworks/api/sesiones_en_vivo_router.py`, `schemas.py`, `dependencies.py` (modificados)

### Tests

- `tests/unit/inc6/test_participacion_en_vivo.py`, `test_unirse_a_sesion_en_vivo_use_case.py` (nuevos)
- `tests/unit/inc6/_fakes.py`, `test_actividad_evaluativa_en_vivo.py`, `test_crear_sesion_en_vivo_use_case.py` (modificados)
- `tests/integration/inc6/_helpers.py`, `test_sesiones_en_vivo_unirse_router.py` (nuevos)
- `tests/features/inc6/US-6.1.3-unirse-sesion-en-vivo.feature` (nuevo)
- `tests/step_defs/inc6/test_us_6_1_3_steps.py` (nuevo)

### Documentación

- `docs/plans/inc6/US-6.1.3-context.md`, `US-6.1.3-plan.md`
- `docs/specs/inc6/US-6.1.3.md` (estado → `Implementada`)
- `docs/reports/inc6/US-6.1.3-report.md` (este archivo)
- `quality/reports/inc6/US-6.1.3-quality.json`, `-codeguard.json`, `-coverage.json`

---

## Desafíos y Soluciones

### Desafío 1: Probar `EnCurso` y `Finalizada` sin una US que los produzca

**Descripción:** Los escenarios de unión tardía y de sesión finalizada necesitan una sesión en
esos estados, pero `IniciarSesionEnVivo` es `US-6.1.4` y finalizar es Iteración 2.

**Solución:** Los tests siembran directamente un evento `SesionEnVivoIniciada`/
`SesionEnVivoFinalizada` (payload mínimo) en el stream de la sesión vía `EventStorePort`, después
de crearla con `POST /sesiones-en-vivo`. Y `reconstruir()` aplica solo `estado` por `event_type`,
sin inventar payloads que definen las US siguientes.

### Desafío 2: Tabla de proyección o query sobre `events`

**Descripción:** La spec dejaba a Fase 2 si `participantes_por_sesion` era una tabla nueva o una
proyección sobre `events`.

**Solución:** Query de lectura sobre los eventos `EstudianteUnido` (filtro JSONB), mismo criterio
que `EvaluacionActivaQueryPort` en `US-3.2.4`: sin migración y sin riesgo de desincronización a
esta escala. Reversible si el volumen cambia.

### Desafío 3: Cambiar la firma de un controller rompe tests de la US anterior

**Descripción:** Al inyectar un segundo use case en `SesionesEnVivoController`, el test unitario
de `US-6.1.2` que lo construía con uno solo dejó de funcionar.

**Solución:** Se actualizó ese test. Conviene grepear los `Controller(` de los tests antes de
tocar una firma.

---

## Cambios no Previstos

- Actualización de `tests/unit/inc6/test_crear_sesion_en_vivo_use_case.py` (Desafío 3) y nuevo
  `tests/integration/inc6/_helpers.py`, compartido entre integración y BDD.
- Ningún desvío de diseño respecto del plan aprobado.

---

## Criterios de Aceptación

- [x] Unión mientras la sesión está en espera: se crea la `ParticipacionEnVivo`, aparece en `participantes_por_sesion` y el Docente conectado recibe la lista actualizada
- [x] Unión tardía con la sesión en curso: la participación se crea, sin respuestas previas
- [x] Unión idempotente: 200 sin crear una segunda `ParticipacionEnVivo`
- [x] Sesión finalizada → `SesionYaFinalizada` (422)
- [x] Sesión inexistente → `SesionNoExiste` (404)

**Estado:** 5/5 cumplidos

---

## Próximos Pasos

- [ ] `US-6.1.4` — Docente inicia la sesión: emite el `SesionEnVivoIniciada` real y define su
  payload (hoy `reconstruir()` solo lo usa para `estado`); primer broadcast de un evento de
  dominio de la sesión. Cuando exista, los tests de unión tardía pueden usarlo en lugar de la
  siembra
- [ ] La sala de espera del Docente muestra solo ids: mostrar nombres requerirá un puerto a
  Identidad, alcance de la iteración de frontend (todavía sin asignar en `inc6-candidatas.md`)

---

## Lecciones Aprendidas

- ✅ Aplicar la lección de `US-6.1.2` (suite completa primero, `codeguard` después y en serie)
  dio un cierre limpio: 1286 passed sin errores y CodeGuard sin timeouts de herramienta.
- ✅ Elegir la variante barata cuando la spec deja "a decidir en Fase 2" (query sobre `events`
  en vez de tabla propia) evitó una migración y una proyección desincronizable.
- ✅ Diferir `reconstruir()` en `US-6.1.2` fue correcto: recién acá hay consumidor, y quedó
  acotado a `estado`.
- ⚠️ Agregar un use case al constructor de un controller rompe los tests de la US anterior:
  grepear antes de tocar la firma.
- 💡 `TestClient` sincrónico + `asyncio.run` para preparar datos permite verificar el broadcast
  real por WebSocket junto a un request HTTP, sin fixtures async especiales (`NullPool`).

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-09-19
