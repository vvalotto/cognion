# Reporte de Implementación: US-ADJ-46 - Docente consulta el ranking de preguntas más falladas

## Información General

| Campo | Valor |
|-------|-------|
| **Historia de Usuario** | US-ADJ-46 |
| **Título** | Docente consulta el ranking de preguntas más falladas |
| **Producto** | analytics |
| **Prioridad** | Tercera US de la Iteración 4 del Incremento 5-ADJ — implementada junto con `US-ADJ-45`/`44`/`47` en una sola ejecución/PR |
| **Puntos estimados** | 5 |
| **Fecha inicio** | 2026-09-14 |
| **Fecha fin** | 2026-09-14 |
| **Tiempo real** | 31.2 min (tracking automático) |
| **Estado** | ✅ COMPLETADO |

---

## Resumen Ejecutivo

Tercera US de la Iteración 4 del Incremento 5-ADJ: el Docente puede ver un ranking de las
preguntas puntuales con mayor tasa de error (`GET /analytics/materias/{id}/ranking-preguntas-falladas?comision_id=`,
RF-22) — reusa exactamente la misma fuente que `ObtenerTasaErrorPorTemaUseCase` (`US-4.2.4`,
RF-17), cambiando la clave de agrupación de `(unidad_tematica, tema)` a `pregunta_id`.
`MetadatoPreguntaResumen` gana el campo `enunciado`.

**Corrección de arquitectura significativa en Fase 3:** agregar el 6° Use Case a
`AnalyticsController` disparó CRITICAL de CBO (13/10) al correr `designreviewer` localmente
antes de commitear. Se separó en dos controllers — `AnalyticsController` (desempeño
individual del Estudiante, 2 Use Case) y `AnalyticsInformesController` nuevo (informes
agregados de comisión/materia, 4 Use Case: `tasa_error_por_tema`, `desempeno_por_comision`,
`evolucion_temporal_comision`, `ranking_preguntas_falladas`) — mismo criterio de separación
por responsabilidad ya aplicado en Incremento 2 (`BancosController`/`PreguntasController`,
`CuentasController`/`UsuariosController`).

Esta US es solo backend — el frontend (`RankingPreguntasFalladas.tsx`) queda para `US-ADJ-50`.

---

## Componentes Implementados

### Código Fuente (BC Analytics)

- ✅ `src/analytics/entities/ports/pregunta_metadato_consulta_port.py` — `MetadatoPreguntaResumen`
  gana el campo `enunciado`
- ✅ `src/analytics/frameworks/adapters/pregunta_metadato_consulta_port_in_process.py` — trae
  `modelo.texto` como `enunciado`
- ✅ `src/analytics/use_cases/obtener_ranking_preguntas_falladas.py` — nuevo,
  `ObtenerRankingPreguntasFalladasUseCase` + `RankingPreguntaFallada`, con `_ranking_ordenado`
  como función de módulo desde el diseño (lección de `US-ADJ-45`)
- ✅ `src/analytics/interface_adapters/controllers/analytics_controller.py` — reducido a 2 Use
  Case (desempeño individual)
- ✅ `src/analytics/interface_adapters/controllers/analytics_informes_controller.py` — nuevo,
  4 Use Case (informes agregados)
- ✅ `src/analytics/frameworks/dependencies.py` — `get_analytics_informes_controller` nuevo
- ✅ `src/analytics/frameworks/api/schemas.py` — `RankingPreguntaFalladaResponse`
- ✅ `src/analytics/frameworks/api/analytics_router.py` — endpoint nuevo (rol `docente`), 4
  endpoints existentes migrados al controller nuevo

**Total archivos de producción modificados/creados:** 8 (2 nuevos, 6 modificados)

---

### Tests

#### Tests Unitarios
- ✅ `tests/unit/inc4/test_obtener_ranking_preguntas_falladas.py` — 8 tests (nuevo)
- ✅ `tests/unit/inc4/test_analytics_controller.py` — reescrito para el controller reducido
- ✅ `tests/unit/inc4/test_analytics_informes_controller.py` — nuevo, 6 tests para el
  controller separado
- ✅ `tests/unit/inc4/test_pregunta_metadato_consulta_port.py`,
  `test_obtener_tasa_error_por_tema.py` — instancias de `MetadatoPreguntaResumen` actualizadas
  con `enunciado`

**Total tests unitarios del proyecto:** 532/532 pasando (100% coverage en `src/analytics`)

#### Tests de Integración
- ✅ `tests/integration/inc4/test_analytics_router_ranking_preguntas_falladas.py` — 6 tests
  nuevos (endpoint completo vía `AsyncClient`)

**Total tests de integración del proyecto:** 374/374 pasando

#### Escenarios BDD
- ✅ `tests/features/inc5-adj/US-ADJ-46-ranking-preguntas-falladas.feature` — 6 escenarios
- ✅ `tests/step_defs/inc4/test_us_adj_46_steps.py` — steps nuevo

**Total escenarios BDD del proyecto:** 263/263 pasando

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **Pylint** | 9.82/10 | ≥ 8.0 | ✅ |
| **Complejidad Ciclomática (máx/función)** | 9 | ≤ 10 | ✅ |
| **Índice Mantenibilidad (mín/archivo)** | 50.52 | > 20 | ✅ |
| **Coverage** (entities/use_cases/interface_adapters) | 100% | ≥ 95% | ✅ |
| **mypy** (`src/` completo) | 0 errores | 0 errores | ✅ |
| **DesignReviewer** (local, `src/analytics/`) | 0 CRITICAL (tras el fix de CBO) | 0 CRITICAL | ✅ |
| **CodeGuard** (12 archivos, acumulado de la branch) | 8 errores, 109 warnings | 0 CRITICAL | ✅ |

Fuente completa: `quality/reports/inc5-adj/US-ADJ-46-quality.json`.

### Detalle de CodeGuard

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 12 |
| PEP8 | 0 | 1 | 11 |
| Complexity | 0 | 0 | 12 |
| DeadCode | 8 | 90 | 1 |
| Maintainability | 0 | 0 | 12 |
| Pylint | 0 | 0 | 12 |
| Spelling | 0 | 18 | 4 |
| Types | 0 | 0 | 11 |
| UnusedImports | 0 | 0 | 12 |

Reporte corre sobre el acumulado de la branch (US-ADJ-44+45+46) — comparten el mismo diff
contra `develop`. Los 8 errores de `DeadCode` son falso positivo de `vulture` sobre parámetros
de métodos abstractos — mismo patrón ya aceptado en `US-ADJ-44`/`45`.

---

## Criterios de Aceptación

- [x] Materia completa, sin filtrar por comisión — 5 preguntas ordenadas por tasa descendente
- [x] Acotado a una comisión — ranking calculado solo sobre esas respuestas
- [x] Tasa de error prevalece sobre conteo bruto — 1/1 (100%) antes que 10/50 (20%)
- [x] Materia sin ninguna pregunta presentada — 200 con lista vacía
- [x] Comisión que no pertenece a la materia — 422
- [x] Rol distinto de Docente — 403

**Estado:** 6/6 cumplidos

---

## Desafíos y Soluciones

### Desafío 1: CRITICAL de CBO al agregar el 6° Use Case al controller

**Descripción:** `AnalyticsController` venía creciendo desde `US-4.1.2` — con `US-ADJ-44`/`45`
ya tenía 5 Use Case; agregar el 6° (`ObtenerRankingPreguntasFalladasUseCase`) empujó el CBO a
13/10.

**Solución:** Correr `designreviewer src/analytics/ --config pyproject.toml` localmente
*antes* de commitear (no esperar al pre-push) permitió detectarlo y corregirlo en la misma
tarea. Separación por responsabilidad: `AnalyticsController` (desempeño individual del
Estudiante) vs `AnalyticsInformesController` (informes agregados de comisión/materia) — mismo
criterio ya aplicado en Incremento 2.

**Aprendizaje:** Antes de agregar cualquier Use Case a un controller que ya tiene 4 o más,
correr `designreviewer` local es más barato que descubrirlo en el pre-push (evita un commit de
"fix" adicional). Documentado para `US-ADJ-47`, que agrega un 5° Use Case a algún controller.

---

## Documentación Actualizada

- [x] Docstrings agregados/actualizados en los 8 archivos tocados
- [x] `docs/plans/US-ADJ-46-plan.md` completado con estado, métricas y lecciones aprendidas
- [x] `CHANGELOG.md` actualizado (`[Unreleased]`)
- [x] `quality/reports/inc5-adj/US-ADJ-46-quality.json` y `-codeguard.json` generados
- [ ] `docs/plans/inc5-adj/inc5-adj-candidatas.md`/`CLAUDE.md` — se actualizan al cierre de
  sesión (`/checkpoint`), no en esta fase

---

## Tiempo Invertido

| Fase | Tiempo Real |
|------|-------------|
| Fase 0 — Validación de Contexto | 20 s |
| Fase 1 — Generación de Escenarios BDD | 17 s |
| Fase 2 — Plan de Implementación | 39 s |
| Fase 3 — Implementación (incluye fix de CBO) | 628 s |
| Fase 4 — Tests Unitarios | 53 s |
| Fase 5 — Tests de Integración | 245 s |
| Fase 6 — Validación BDD | 248 s |
| Fase 7 — Quality Gates | 512 s |
| Fase 8 — Documentación | 70 s |
| **TOTAL (Fases 0-8)** | **1871 s (≈ 31.2 min)** |

---

## Lecciones Aprendidas

### Lo que Funcionó Bien

1. Detectar el CRITICAL de CBO corriendo `designreviewer` local antes de commitear, no
   esperando al pre-push — ahorró un ciclo completo de commit/push/fix.
2. Diseñar `_ranking_ordenado` como función de módulo desde el arranque (lección de
   `US-ADJ-45`) evitó cualquier CC CRITICAL en el Use Case nuevo.

### Recomendaciones para Próximas Historias

1. `US-ADJ-47` (completitud por actividad) también agrega un Use Case a algún controller —
   correr `designreviewer` local antes de commitear, mismo criterio que esta US.

---

## Próximos Pasos

### Historias Relacionadas

- [ ] `US-ADJ-47` — Docente consulta la completitud de una actividad puntual (RF-23, backend)
- [ ] `US-ADJ-50` — Docente ve el ranking de preguntas más falladas (RF-22, frontend — consume esta US)

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-09-14
