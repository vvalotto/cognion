# Reporte de Implementación: US-ADJ-47 - Docente consulta la completitud de una actividad puntual

## Información General

| Campo | Valor |
|-------|-------|
| **Historia de Usuario** | US-ADJ-47 |
| **Título** | Docente consulta la completitud de una actividad puntual |
| **Producto** | analytics |
| **Prioridad** | Cuarta y última US de la Iteración 4 del Incremento 5-ADJ — implementada junto con `US-ADJ-44`/`45`/`46` en una sola ejecución/PR |
| **Puntos estimados** | 5 |
| **Fecha inicio** | 2026-09-14 |
| **Fecha fin** | 2026-09-14 |
| **Tiempo real** | ~28.9 min de trabajo efectivo (ver nota en "Tiempo Invertido") |
| **Estado** | ✅ COMPLETADO |

---

## Resumen Ejecutivo

Cuarta y última US de la Iteración 4 del Incremento 5-ADJ: el Docente puede ver, para una
actividad puntual, el estado de cada estudiante del roster aplicable — sin iniciar, en curso,
suspendida o finalizada (`GET /analytics/actividades/{actividad_id}/completitud`, RF-23). El
roster se resuelve por la(s) comisión(es) restringida(s) de la actividad, o toda la materia si
no hay restricción — mismo significado de `comisiones_ids` vacío ya usado en
`ActividadEvaluativaPeriodoAbierto`.

**Dos correcciones de arquitectura detectadas localmente en Fase 3** (antes de commitear, no en
el pre-push): (1) agregar el 5° Use Case a `AnalyticsInformesController` disparó CRITICAL de
CBO (11/10) — resuelto con un tercer controller, `AnalyticsCompletitudController`, mismo
criterio de separación por responsabilidad ya aplicado en `US-ADJ-46`; (2) los 2 métodos nuevos
del puerto empujaron a `EvaluacionDesempenoConsultaPortInProcess` a CRITICAL de WMC (29/25) —
resuelto extrayendo `_streams_de_estudiante`/`_resumenes_filtrados` como funciones de módulo.

Esta US es solo backend — el frontend (`CompletitudActividad.tsx`) queda para `US-ADJ-51`.
Cierra completo el backend de la Iteración 4 (Analytics RF-20 a RF-23).

---

## Componentes Implementados

### Código Fuente (BC Analytics)

- ✅ `src/analytics/entities/errors.py` — `ActividadNoExiste(actividad_id)` nuevo
- ✅ `src/analytics/entities/ports/evaluacion_desempeno_consulta_port.py` — `ActividadResumen`
  (dataclass) + 2 métodos abstractos nuevos: `obtener_actividad_resumen`,
  `listar_estados_de_actividad`
- ✅ `src/analytics/frameworks/adapters/evaluacion_desempeno_consulta_port_in_process.py` —
  implementación de ambos métodos (reusa `_streams_de_actividades` y
  `ActividadEvaluativaPeriodoAbierto.reconstruir()` para el primero; `Evaluacion.reconstruir()`
  + función de módulo nueva `_estados_por_estudiante` para el segundo) + refactor de
  `listar_evaluaciones_finalizadas` (extrae `_streams_de_estudiante`/`_resumenes_filtrados`
  para bajar el WMC de la clase)
- ✅ `src/analytics/use_cases/obtener_completitud_por_actividad.py` — nuevo,
  `ObtenerCompletitudPorActividadUseCase` + `CompletitudFila`/`CompletitudResumen`/
  `CompletitudPorActividad`, con `_roster_aplicable`/`_detalle_de`/`_resumen_de` como funciones
  de módulo desde el diseño (lección de `US-ADJ-45`/`46`)
- ✅ `src/analytics/interface_adapters/controllers/analytics_completitud_controller.py` —
  nuevo, tercer controller del BC (un solo Use Case)
- ✅ `src/analytics/interface_adapters/controllers/analytics_informes_controller.py` —
  docstring actualizado documentando el intento de agregar el 5° Use Case y el fix
- ✅ `src/analytics/frameworks/dependencies.py` — `get_analytics_completitud_controller` nuevo
- ✅ `src/analytics/frameworks/api/schemas.py` — `CompletitudFilaResponse`,
  `CompletitudResumenResponse`, `CompletitudPorActividadResponse`
- ✅ `src/analytics/frameworks/api/analytics_router.py` — endpoint nuevo (rol `docente`),
  mapea `ActividadNoExiste` → 404

**Total archivos de producción modificados/creados:** 9 (2 nuevos, 7 modificados)

---

### Tests

#### Tests Unitarios
- ✅ `tests/unit/inc4/test_obtener_completitud_por_actividad.py` — 5 tests (nuevo)
- ✅ `tests/unit/inc4/test_analytics_completitud_controller.py` — 1 test (nuevo)
- ✅ `tests/unit/inc4/test_evaluacion_desempeno_consulta_port_in_process.py` — 4 tests nuevos
  (`TestEstadosPorEstudiante`, función pura `_estados_por_estudiante`)
- ✅ 9 `Fake*(EvaluacionDesempenoConsultaPort)` actualizados con los 2 métodos nuevos del
  puerto (incluye un fake inline en `test_obtener_desempeno_estudiante.py`)

**Total tests unitarios del proyecto:** 542/542 pasando (100% coverage en `src/analytics`)

#### Tests de Integración
- ✅ `tests/integration/inc4/test_evaluacion_desempeno_consulta_port.py` — 8 tests nuevos
  (`TestObtenerActividadResumen` ×2, `TestListarEstadosDeActividad` ×6)
- ✅ `tests/integration/inc4/test_analytics_router_completitud.py` — 5 tests nuevos (endpoint
  completo vía `AsyncClient`)

**Total tests de integración del proyecto:** 387/387 pasando

#### Escenarios BDD
- ✅ `tests/features/inc5-adj/US-ADJ-47-completitud-por-actividad.feature` — 4 escenarios
- ✅ `tests/step_defs/inc4/test_us_adj_47_steps.py` — steps nuevo

**Total escenarios BDD del proyecto:** 267/267 pasando

**Total combinado (unit + integration + step_defs) del proyecto:** 1196/1196 pasando

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **Pylint** | 9.69/10 | ≥ 8.0 | ✅ |
| **Complejidad Ciclomática (máx/función)** | 9 | ≤ 10 | ✅ |
| **Índice Mantenibilidad (mín/archivo)** | 47.51 | > 20 | ✅ |
| **Coverage** (entities/use_cases/interface_adapters) | 100% | ≥ 95% | ✅ |
| **mypy** (`src/` completo) | 0 errores | 0 errores | ✅ |
| **DesignReviewer** (local, `src/analytics/`) | 0 CRITICAL (tras los 2 fixes) | 0 CRITICAL | ✅ |
| **CodeGuard** (31 archivos, acumulado de la branch) | 24 errores, 177 warnings | 0 CRITICAL | ✅ |

Fuente completa: `quality/reports/inc5-adj/US-ADJ-47-quality.json`.

### Detalle de CodeGuard

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 31 |
| PEP8 | 0 | 2 | 29 |
| Complexity | 0 | 0 | 31 |
| DeadCode | 14 | 141 | 10 |
| Maintainability | 0 | 0 | 31 |
| Pylint | 9 | 0 | 22 |
| Spelling | 0 | 34 | 17 |
| Types | 0 | 0 | 21 |
| UnusedImports | 1 | 0 | 30 |

Reporte corre sobre el acumulado de la branch (US-ADJ-44+45+46+47) — comparten el mismo diff
contra `develop`. Los 14 errores de `DeadCode` son el mismo falso positivo de `vulture` sobre
parámetros de métodos abstractos ya aceptado en `US-ADJ-44`/`45`/`46`. Los 9 errores de
`Pylint` ("Could not extract pylint score from output") son sobre `__init__.py` vacíos, sin
código que puntuar — no un problema real. El error de `UnusedImports` ("pylint execution timed
out (>5s)") sobre el adapter grande del BC es el mismo patrón de timeout de herramienta ya
documentado en `CLAUDE.md` para el check de tipos (`software_limpio#70`) — mypy dedicado, la
fuente de verdad local, no reporta ningún import sin usar en ese archivo.

---

## Criterios de Aceptación

- [x] Actividad restringida a una comisión, estados mixtos — 200 con resumen exacto y detalle
  de los 4 estudiantes con su estado exacto (incluye `sin_iniciar` para quien nunca inició)
- [x] Actividad sin restricción de comisión — el roster del detalle incluye ambas comisiones
- [x] Actividad inexistente — 404
- [x] Rol distinto de Docente — 403

**Estado:** 4/4 cumplidos

---

## Desafíos y Soluciones

### Desafío 1: CRITICAL de CBO al agregar el 5° Use Case al controller

**Descripción:** `AnalyticsInformesController` ya tenía 4 Use Case desde `US-ADJ-46`; agregar
el 5° (`ObtenerCompletitudPorActividadUseCase`) empujó el CBO a 11/10.

**Solución:** Corrido `designreviewer src/analytics/ --config pyproject.toml` localmente antes
de commitear (lección explícita de `US-ADJ-46`, anotada en `docs/plans/inc5-adj/US-ADJ-47-context.md`).
Se creó `AnalyticsCompletitudController`, tercer controller del BC, con ese único Use Case.

**Aprendizaje:** Confirma la regla ya documentada: cualquier Use Case nuevo sobre un controller
con 4 o más dispara CBO CRITICAL en este BC — separar en un controller propio en vez de forzar
el límite es más barato que descubrirlo en el pre-push.

### Desafío 2: CRITICAL de WMC en el adapter del puerto

**Descripción:** Agregar `obtener_actividad_resumen`/`listar_estados_de_actividad` a
`EvaluacionDesempenoConsultaPortInProcess` (más la función de módulo `_estados_por_estudiante`)
empujó el WMC de la clase de bajo el umbral a 29/25 — hallazgo nuevo, no visto en `US-ADJ-44`
a `46`, porque el adapter venía acumulando métodos desde `US-4.1.1`.

**Solución:** Extraídas `_streams_de_estudiante` y `_resumenes_filtrados` como funciones de
módulo desde `listar_evaluaciones_finalizadas` (el método con mayor CC de la clase, 9), que no
había sido tocado por ninguna US anterior. WMC bajó de 29 a 23.

**Aprendizaje:** El chequeo de WMC (complejidad total de una clase, no solo CC por método) no
se había disparado antes porque ningún método nuevo agregado en `US-4.2.x`/`US-ADJ-44/45/46`
coincidió con que la clase ya estuviera cerca del umbral. Al extender un adapter/controller que
ya acumula muchos métodos, correr `designreviewer` local cubre tanto CBO como WMC — no alcanza
con mirar solo CC por método (Fase 7) o solo CBO de controllers.

---

## Documentación Actualizada

- [x] Docstrings agregados/actualizados en los 9 archivos tocados
- [x] `docs/plans/inc5-adj/US-ADJ-47-plan.md` completado con estado, métricas y lecciones aprendidas
- [x] `CHANGELOG.md` actualizado (`[Unreleased]`)
- [x] `quality/reports/inc5-adj/US-ADJ-47-quality.json` y `-codeguard.json` generados
- [ ] `docs/plans/inc5-adj/inc5-adj-candidatas.md`/`CLAUDE.md` — se actualizan al cierre de
  sesión (`/checkpoint`), no en esta fase

---

## Tiempo Invertido

| Fase | Tiempo Real |
|------|-------------|
| Fase 0 — Validación de Contexto | 32 s |
| Fase 1 — Generación de Escenarios BDD | 16 s |
| Fase 2 — Plan de Implementación | 61 s |
| Fase 3 — Implementación (incluye fix de CBO y de WMC) | 792 s |
| Fase 4 — Tests Unitarios | 114 s |
| Fase 5 — Tests de Integración | 302 s |
| Fase 6 — Validación BDD | 369 s |
| Fase 7 — Quality Gates | 13624 s (ver nota) |
| Fase 8 — Documentación | 46 s |
| **TOTAL (Fases 0-8, sin la Fase 7 distorsionada)** | **1732 s (≈ 28.9 min)** |

**Nota sobre la Fase 7:** el tracking automático mide tiempo de reloj, no tiempo efectivo de
trabajo. La sesión se cerró (apagado de la máquina) a mitad de la Fase 7, con el tracker
corriendo; al reabrir la sesión el reloj siguió sumando desde donde había quedado en vez de
descontar la pausa real. El trabajo efectivo de la Fase 7 (coverage, pylint, radon, CodeGuard,
DesignReviewer) fue de aproximadamente 6-8 minutos en total, repartidos en dos tramos.
**Lección para el skill/tracker:** al anticipar un cierre de sesión a mitad de una fase, invocar
un `pause` explícito del tracker (si existe el comando) o al menos dejarlo anotado, para que el
tiempo reportado no incluya el intervalo entre sesiones.

---

## Lecciones Aprendidas

### Lo que Funcionó Bien

1. Anticipar en `docs/plans/inc5-adj/US-ADJ-47-context.md` las 4 lecciones de `US-ADJ-44`/`45`/`46`
   (actualizar Fakes en la misma tarea, extraer agregación a funciones de módulo desde el
   diseño, correr `designreviewer` local antes de commitear, nunca correr suites en paralelo)
   evitó repetir cualquiera de esos incidentes en esta US.
2. Diseñar `_detalle_de`/`_resumen_de` como funciones de módulo desde el arranque evitó
   cualquier CC CRITICAL en el Use Case nuevo (CC máx 9 en `_resumen_de`, justo bajo el umbral).
3. Correr `designreviewer` local proactivamente detectó **dos** CRITICAL distintos (CBO y WMC)
   antes de cualquier commit — ninguno llegó al pre-push.

### Recomendaciones para Próximas Historias

1. Al extender un adapter/controller que ya acumula varios métodos (no solo al agregar un Use
   Case a un controller con 4+), correr `designreviewer` local cubre tanto CBO como WMC —
   agregar esta verificación como regla explícita, no solo la de CBO en controllers.
2. Si se anticipa cerrar la sesión a mitad de una fase del tracker, buscar o agregar un comando
   de pausa explícita para que el tiempo reportado no quede distorsionado por el intervalo
   entre sesiones (ver nota en "Tiempo Invertido").

---

## Próximos Pasos

### Historias Relacionadas

- [ ] `US-ADJ-51` — Docente ve la completitud de una actividad puntual (RF-23, frontend —
  consume esta US)
- [ ] Con `US-ADJ-44`/`45`/`46`/`47` completas, cierra el backend completo de la Iteración 4
  del Incremento 5-ADJ (Analytics RF-20 a RF-23) — queda pendiente commitear, pushear la rama
  compartida y crear el PR único que cubre las cuatro US (decisión de Víctor)

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-09-14
