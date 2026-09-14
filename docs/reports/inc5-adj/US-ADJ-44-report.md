# Reporte de Implementación: US-ADJ-44 - Docente consulta el desempeño de una Comisión completa

## Información General

| Campo | Valor |
|-------|-------|
| **Historia de Usuario** | US-ADJ-44 |
| **Título** | Docente consulta el desempeño de una Comisión completa |
| **Producto** | analytics (+ un cambio puntual en actividad_evaluativa) |
| **Prioridad** | Primera US de la Iteración 4 del Incremento 5-ADJ (Analytics RF-20 a RF-23) — backend del par RF-20 |
| **Puntos estimados** | 5 |
| **Fecha inicio** | 2026-09-14 |
| **Fecha fin** | 2026-09-14 |
| **Tiempo real** | 53.1 min (tracking automático) |
| **Estado** | ✅ COMPLETADO |

---

## Resumen Ejecutivo

Primera US de la Iteración 4 del Incremento 5-ADJ: el Docente puede consultar, para una
Comisión completa, el % de aciertos acumulado y las actividades pendientes de cada estudiante
(`GET /analytics/materias/{materia_id}/comisiones/{comision_id}/desempeno`, RF-20), y desde ahí
pedir la revisión completa de una evaluación puntual de cualquier estudiante — para eso, el
guard de `GET /evaluaciones/{id}/revision` (BC Actividad Evaluativa) se amplió de
`require_estudiante` a `require_estudiante_o_docente`, sin verificación de pertenencia
Docente↔Materia (mismo precedente de RBAC por rol ya aplicado en `US-4.2.1`).

**Decisión de diseño tomada en Fase 2:** `listar_actividades_abiertas` (nuevo método de
`EvaluacionDesempenoConsultaPort`) necesita el estado *actual* de
`ActividadEvaluativaPeriodoAbierto` — `fecha_cierre` puede haber cambiado por
`PeriodoDisponibilidadModificado` (`US-3.3.1`), `cerrada_manualmente` por
`ActividadEvaluativaCerrada` (`US-3.3.2`). En vez de reimplementar el replay evento por evento
dentro del adapter de Analytics, se reusa directamente
`ActividadEvaluativaPeriodoAbierto.reconstruir()` — entidad pura de `entities/`, sin ORM ni
FastAPI, mismo criterio de excepción ya documentado para `EventoModel` en ese mismo adapter
("único punto de Analytics que importa código de otro BC"). Evita duplicar `_aplicar_evento` de
ese aggregate y el riesgo de que diverja si gana un evento nuevo.

Esta US es solo backend — el frontend (`DesempenoPorComision.tsx`, con los dos niveles de
drill-down) queda para `US-ADJ-48`.

---

## Componentes Implementados

### Código Fuente (BC Analytics)

- ✅ `src/analytics/entities/ports/evaluacion_desempeno_consulta_port.py` — método abstracto `listar_actividades_abiertas(materia_id, comision_id)` agregado
- ✅ `src/analytics/frameworks/adapters/evaluacion_desempeno_consulta_port_in_process.py` — implementación (reusa `ActividadEvaluativaPeriodoAbierto.reconstruir()`), funciones de módulo `_a_evento_almacenado`/`_actividad_abierta_y_visible`
- ✅ `src/analytics/use_cases/obtener_desempeno_por_comision.py` — nuevo, `ObtenerDesempenoPorComisionUseCase` + `DesempenoComisionFila`
- ✅ `src/analytics/interface_adapters/controllers/analytics_controller.py` — 3er Use Case, método `obtener_desempeno_por_comision`
- ✅ `src/analytics/frameworks/dependencies.py` — `get_analytics_controller` cablea el Use Case nuevo
- ✅ `src/analytics/frameworks/api/schemas.py` — `DesempenoComisionFilaResponse`
- ✅ `src/analytics/frameworks/api/analytics_router.py` — `GET /materias/{materia_id}/comisiones/{comision_id}/desempeno` (rol `docente`)

### Código Fuente (BC Actividad Evaluativa — guard ampliado)

- ✅ `src/actividad_evaluativa/use_cases/obtener_revision_evaluacion.py` — `execute()` gana `verificar_propietario: bool = True`
- ✅ `src/actividad_evaluativa/interface_adapters/controllers/revision_controller.py` — pasa el flag al Use Case
- ✅ `src/actividad_evaluativa/frameworks/dependencies.py` — `require_estudiante_o_docente` nueva
- ✅ `src/actividad_evaluativa/frameworks/api/revision_router.py` — guard ampliado, `verificar_propietario = usuario.rol is TipoPerfil.ESTUDIANTE`

**Total archivos de producción modificados/creados:** 11 (1 nuevo, 10 modificados)

---

### Tests

#### Tests Unitarios
- ✅ `tests/unit/inc4/test_obtener_desempeno_por_comision.py` — 7 tests (nuevo)
- ✅ `tests/unit/inc4/test_evaluacion_desempeno_consulta_port_in_process.py` — 5 tests nuevos (`TestActividadAbiertaYVisible`)
- ✅ `tests/unit/inc3/test_obtener_revision_evaluacion_use_case.py` — 2 tests nuevos (`verificar_propietario`)
- ✅ `tests/unit/inc4/test_analytics_controller.py`, `test_obtener_tasa_error_por_tema.py`, `test_obtener_desempeno_estudiante.py` — fakes ampliados con `listar_actividades_abiertas` (método abstracto nuevo del puerto), 1 test de delegación nuevo

**Total tests unitarios del proyecto:** 511/511 pasando (100% coverage en `src/analytics`)

#### Tests de Integración
- ✅ `tests/integration/inc4/test_evaluacion_desempeno_consulta_port.py` — `TestListarActividadesAbiertas`, 6 tests nuevos contra Postgres real
- ✅ `tests/integration/inc4/test_analytics_router_desempeno_por_comision.py` — 5 tests nuevos (endpoint completo vía `AsyncClient`)
- ✅ `tests/integration/inc3/test_finalizar_revision_api_integration.py` — 2 tests nuevos (drill-down de Docente, 404), 1 test corregido (`administrador`, no `docente`, es ahora el rol insuficiente)

**Total tests de integración del proyecto:** 354/354 pasando

#### Escenarios BDD
- ✅ `tests/features/inc5-adj/US-ADJ-44-desempeno-por-comision.feature` — 7 escenarios
- ✅ `tests/step_defs/inc4/test_us_adj_44_steps.py` — steps nuevo

**Total escenarios BDD del proyecto:** 251/251 pasando

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **Pylint** | 9.89/10 | ≥ 8.0 | ✅ |
| **Complejidad Ciclomática (máx/función)** | 9 | ≤ 10 | ✅ |
| **Índice Mantenibilidad (mín/archivo)** | 50.54 | > 20 | ✅ |
| **Coverage** (entities/use_cases/interface_adapters) | 100% | ≥ 95% | ✅ |
| **mypy** (`src/` completo) | 0 errores | 0 errores | ✅ |
| **CodeGuard** (11 archivos modificados/agregados) | 7 errores, 87 warnings | 0 CRITICAL | ✅ |

Fuente completa: `quality/reports/inc5-adj/US-ADJ-44-quality.json`.

### Detalle de CodeGuard

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 11 |
| PEP8 | 0 | 4 | 7 |
| Complexity | 0 | 0 | 11 |
| DeadCode | 6 | 70 | 2 |
| Maintainability | 0 | 0 | 11 |
| Pylint | 0 | 1 | 10 |
| Spelling | 0 | 12 | 2 |
| Types | 0 | 0 | 10 |
| UnusedImports | 1 | 0 | 10 |

Los 6 errores de `DeadCode` son falso positivo de `vulture` sobre los parámetros de los 3
métodos abstractos de `EvaluacionDesempenoConsultaPort` (firma de interfaz ABC, mismo patrón ya
presente en los métodos preexistentes de ese archivo). El error de `UnusedImports` es el bug ya
documentado en `CLAUDE.md` (`vvalotto/software_limpio#70`): el check de tipos integrado en
CodeGuard no usa `--cache-dir` y cae en timeout en corridas en frío. El pylint dedicado (fuera
de CodeGuard) corrió limpio: 9.89/10.

---

## Criterios de Aceptación

- [x] Comisión con estudiantes en distinto estado — % acumulado y 0 pendientes para quien ya finalizó todo, "Sin datos" (`null`) y 1 pendiente para quien no rindió ninguna evaluación
- [x] Comisión sin ninguna evaluación finalizada — 200 con todos los estudiantes en "Sin datos"
- [x] Comisión que no pertenece a la materia — 422 (`ComisionNoPerteneceAMateria`)
- [x] Sin autenticación — 401
- [x] Rol distinto de Docente — 403
- [x] Drill-down a la revisión de una evaluación ajena (Docente) — 200 con el detalle completo
- [x] Rol ni Docente ni Estudiante dueño (Administrador) pide la revisión — 403

**Estado:** 7/7 cumplidos

---

## Arquitectura Implementada

### Patrón Aplicado

Clean Architecture BC-first (`entities → use_cases → interface_adapters → frameworks`). El
cambio cruza dos BC: Analytics (nuevo endpoint completo) y Actividad Evaluativa (guard
ampliado de un endpoint ya existente, sin nueva regla de negocio — la validación de
pertenencia queda deliberadamente fuera de alcance, ver "Desafíos y Soluciones").

### Flujo de Datos

```
GET /analytics/materias/{id}/comisiones/{id}/desempeno (rol docente)
  → AnalyticsController.obtener_desempeno_por_comision
    → ObtenerDesempenoPorComisionUseCase
      → ComisionConsultaPort.listar_comisiones_por_materia (valida pertenencia)
      → ComisionConsultaPort.listar_estudiantes (roster)
      → EvaluacionDesempenoConsultaPort.listar_actividades_abiertas (nuevo)
          → reconstruye ActividadEvaluativaPeriodoAbierto.reconstruir() por stream
      → EvaluacionDesempenoConsultaPort.listar_evaluaciones_finalizadas (por estudiante)
      → arma DesempenoComisionFila (% acumulado | None, actividades_pendientes)

GET /evaluaciones/{id}/revision (rol estudiante O docente)
  → RevisionController.obtener_revision(evaluacion_id, usuario_id, verificar_propietario)
    → ObtenerRevisionEvaluacionUseCase.execute(..., verificar_propietario)
      → verificar_propietario=True (Estudiante): exige evaluacion.estudiante_id == usuario_id
      → verificar_propietario=False (Docente): sin ese chequeo — RBAC por rol alcanza
```

---

## Desafíos y Soluciones

### Desafío 1: Reconstruir el estado real de una actividad sin duplicar su replay

**Descripción:** `listar_actividades_abiertas` necesita `fecha_cierre`/`cerrada_manualmente`
*actuales*, que pueden diferir del primer evento del stream (`PeriodoDisponibilidadModificado`,
`ActividadEvaluativaCerrada`). El patrón existente en el adapter (`_materia_por_actividad`) solo
lee el primer evento — insuficiente acá.

**Solución:** Importar y reusar `ActividadEvaluativaPeriodoAbierto.reconstruir()` (entidad pura,
sin ORM) en vez de reimplementar el fold de eventos, extendiendo la excepción de import
cross-BC ya documentada para `EventoModel`.

**Aprendizaje:** Cuando un adapter de solo lectura necesita el estado *derivado* de un aggregate
ajeno (no solo un campo invariante), reusar su `reconstruir()` es más seguro que replicar la
lógica de fold — evita que ambas implementaciones diverjan si el aggregate gana un evento nuevo.

---

### Desafío 2: Ampliar un puerto rompe todos sus Fakes de test existentes

**Descripción:** Agregar un método abstracto a `EvaluacionDesempenoConsultaPort` hizo que
`TypeError: Can't instantiate abstract class` apareciera en 4 archivos de test que no tocaba
esta US directamente (`test_obtener_tasa_error_por_tema.py`, `test_obtener_desempeno_estudiante.py`
×2 fakes, `test_analytics_controller.py`), más `AnalyticsController` (constructor con 3er
argumento nuevo).

**Solución:** Agregar `listar_actividades_abiertas` (con `raise NotImplementedError`, ya que
esos tests no la ejercitan) a cada `Fake*(EvaluacionDesempenoConsultaPort)` del proyecto, y
actualizar el helper `_controller()`/`AnalyticsController(...)` en `test_analytics_controller.py`.

**Aprendizaje:** Ampliar un puerto (ABC) exige un barrido de todos sus Fakes en `tests/unit/`,
no solo los del archivo que motivó el cambio — `grep -rn "(EvaluacionDesempenoConsultaPort)"`
antes de correr la suite completa ahorra un ciclo de fallos.

---

## Cambios no Previstos

- `tests/integration/inc3/test_finalizar_revision_api_integration.py::test_rechazo_con_rol_insuficiente`
  usaba `docente_headers` para probar el 403 de rol insuficiente — dejó de aplicar porque
  `docente` ya no es insuficiente desde esta US. Corregido para usar `administrador` (rol que
  sigue sin acceso), y se agregaron 2 tests nuevos que cubren explícitamente el caso que dejó
  de estar cubierto (docente accede con éxito al drill-down; docente recibe 404 por evaluación
  inexistente).

---

## Documentación Actualizada

- [x] Docstrings agregados/actualizados en los 11 archivos tocados
- [x] `docs/plans/US-ADJ-44-plan.md` completado con estado, métricas y lecciones aprendidas
- [x] `CHANGELOG.md` actualizado (`[Unreleased]`)
- [x] `quality/reports/inc5-adj/US-ADJ-44-quality.json` y `-codeguard.json` generados
- [ ] `docs/plans/inc5-adj/inc5-adj-candidatas.md`/`CLAUDE.md` — se actualizan al cierre de sesión (`/checkpoint`), no en esta fase

---

## Tiempo Invertido

| Fase | Tiempo Real |
|------|-------------|
| Fase 0 — Validación de Contexto | 56 s |
| Fase 1 — Generación de Escenarios BDD | 76 s |
| Fase 2 — Plan de Implementación | 186 s |
| Fase 3 — Implementación (11 tareas) | 498 s |
| Fase 4 — Tests Unitarios | 316 s |
| Fase 5 — Tests de Integración | 410 s |
| Fase 6 — Validación BDD | 467 s |
| Fase 7 — Quality Gates | 953 s |
| Fase 8 — Documentación | 61 s |
| **TOTAL (Fases 0-8)** | **3187 s (≈ 53.1 min)** |

> Nota (PRIN-001): estos tiempos son de ejecución del agente, no comparables a estimación
> humana — el skill no registra estimaciones por fase para este perfil.

---

## Lecciones Aprendidas

### Lo que Funcionó Bien

1. Decidir en Fase 2 (antes de codear) reusar `ActividadEvaluativaPeriodoAbierto.reconstruir()`
   evitó una reimplementación de replay que hubiera necesitado sus propios tests de replay.
2. El patrón de fakes con `raise NotImplementedError` para métodos no ejercitados hizo trivial
   parchear los 4 archivos de test rotos por la ampliación del puerto.

### Lo que Puede Mejorar

1. Al planificar una ampliación de puerto (ABC), incluir en el plan de Fase 2 un paso explícito
   de "barrer Fakes existentes" — hubiera evitado descubrirlo recién al correr la suite
   completa en Fase 4.

### Recomendaciones para Próximas Historias

1. `US-ADJ-45` (evolución temporal, RF-21) va a ampliar el mismo puerto de nuevo
   (`obtener_titulos_actividades`) — aplicar la misma disciplina de barrido de Fakes desde el
   arranque de Fase 3, no después del primer fallo en Fase 4.

---

## Próximos Pasos

### Historias Relacionadas

- [ ] `US-ADJ-45` — Docente consulta la evolución temporal de aciertos (RF-21, backend)
- [ ] `US-ADJ-48` — Docente ve "Desempeño por comisión" con drill-down (RF-20, frontend — consume esta US)

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-09-14
