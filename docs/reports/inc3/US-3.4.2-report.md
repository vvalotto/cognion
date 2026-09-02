# Reporte de Implementación: US-3.4.2

## Resumen Ejecutivo

- **Historia de Usuario:** US-3.4.2 - Docente ve sus materias y el listado de actividades de una materia
- **Puntos estimados:** 5
- **Tiempo real:** ~30 min (fases 0-8, ver `docs/plans/inc3/US-3.4.2-plan.md` §Métricas de Tiempo)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-30

---

## Componentes Implementados

### Backend

- ✅ **`titulo`** agregado a `ActividadEvaluativaPeriodoAbierto`/`ActividadEvaluativaCreada`/
  `CrearActividadPeriodoAbiertoUseCase`/schemas — `str = ""` opcional
- ✅ **`ActividadQueryPort`/`ActividadResumen`** (nuevo, `entities/ports/actividad_query_port.py`)
- ✅ **`ListarActividadesUseCase`** (nuevo, `use_cases/listar_actividades.py`)
- ✅ **`SQLAlchemyActividadQueryRepository`** (nuevo, `frameworks/adapters/actividad_query_repository.py`)
  — reconstruye actividades y cuenta evaluaciones activas/finalizadas agrupando `events` en memoria
- ✅ **`ActividadesQueryController`** (nuevo, separado de `ActividadesController`)
- ✅ **`GET /actividades?materia_id={id}`** (nuevo endpoint, rol `docente`) con estado derivado

### Frontend

- ✅ **`actividad-evaluativa-api.ts`**: `titulo` en tipos existentes, nueva `listarActividades()`
- ✅ **`Badge`**: 3 variantes nuevas (`estado-en-curso`, `estado-programada`, `estado-cerrada`)
- ✅ **`MateriasActividades.tsx`** (nueva, `#doc-materias`)
- ✅ **`Actividades.tsx`** (nueva, `#doc-actividades`)
- ✅ **`router.tsx`**: reemplazados los 2 placeholders correspondientes de `US-3.4.1`

---

## Gaps detectados y resueltos (Fase 0/2, antes de escribir código)

1. **`titulo` inexistente en el dominio** — el prototipo HTML y el wireframe piden un título de
   texto libre por actividad (`"Parcial 1 — Unidades 1 a 3"`), pero
   `ActividadEvaluativaPeriodoAbierto` no tenía ese campo. **Consultado con Víctor**: se agrega
   al dominio. Decisión de implementación propia: **opcional** (`str = ""`), no requerido, para
   no romper los 25+ archivos de tests de `US-3.1.2` a `US-3.3.2` que crean actividades sin ese
   campo — verificado corriendo la suite completa (664/664) antes de cerrar la Fase 3.
2. **Conteo de evaluaciones finalizadas** — la spec solo preveía reutilizar
   `EvaluacionActivaQueryPort.listar_no_finalizadas()` (activas). El wireframe/prototipo también
   pide el conteo de finalizadas para actividades cerradas. Resuelto con una consulta propia del
   nuevo `ActividadQueryPort`, sin ensanchar el puerto existente.
3. **Simplificación de `#doc-materias`** (sin impacto de dominio, no requirió aprobación): sin
   "Comisión" ni conteo de actividades por tarjeta — `GET /materias` no expone esos datos.

Detalle completo en `docs/plans/inc3/US-3.4.2-context.md`.

---

## Métricas de Calidad

| Métrica | Backend | Frontend |
|---------|---------|----------|
| Linter | pylint 9.59/10 (≥8.0) | oxlint 0 errores (3 warnings preexistentes) |
| Tipos | mypy 0 errores | `tsc --noEmit` 0 errores |
| Complejidad | CC rank A en todo lo nuevo (≤10) | — |
| Tests | 293/293 (unit+integration+BDD Inc.3), 664/664 (suite completa) | 183/183 (Vitest) |
| Cobertura | 100% (entities/use_cases/interface_adapters) | 91.57% stmts / 93.22% líneas |

Fuente: `quality/reports/inc3/US-3.4.2-quality.json`.

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Backend
- **Unit:** `test_actividad_evaluativa_periodo_abierto.py` (+5 tests `titulo`),
  `test_crear_actividad_periodo_abierto_use_case.py` (+2), `test_listar_actividades_use_case.py`
  (nuevo, 2 tests), `test_actividades_query_controller.py` (nuevo, 1 test)
- **Integración:** `test_actividades_api_integration.py` — +2 tests de `titulo`, +6 tests del
  nuevo `GET /actividades` (estado `en_curso`/`programada`/`cerrada`, conteos, lista vacía,
  401/403)
- **BDD:** `tests/step_defs/inc3/test_us_3_4_2_steps.py` (nuevo) — 3 escenarios de
  `US-3.4.2-listado-materias-actividades-docente.feature`, todos verdes

### Frontend
- **Unit:** `actividad-evaluativa-api.test.ts` — +3 tests (`titulo`, `listarActividades` con y
  sin actividades)
- **Integración:** `router.test.tsx` — +3 tests (listado de materias, listado vacío de
  actividades, tarjeta con estado/conteo/fallback de título)

**Todos los tests pasando:** ✅ 293/293 (Incremento 3 backend), 664/664 (suite completa
backend, sin regresiones), 183/183 (frontend, sin regresiones)

---

## Archivos Creados/Modificados

### Backend
- `entities/actividad_evaluativa_periodo_abierto.py`, `entities/eventos.py`,
  `use_cases/crear_actividad_periodo_abierto.py`, `frameworks/api/schemas.py`,
  `interface_adapters/controllers/actividades_controller.py`,
  `frameworks/api/actividades_router.py` (modificados — campo `titulo`)
- `entities/ports/actividad_query_port.py`, `use_cases/listar_actividades.py`,
  `frameworks/adapters/actividad_query_repository.py`,
  `interface_adapters/controllers/actividades_query_controller.py` (nuevos)
- `frameworks/dependencies.py` (modificado — nueva factory)

### Frontend
- `frontend/src/lib/actividad-evaluativa-api.ts` (modificado)
- `frontend/src/components/ui/badge.tsx` (modificado)
- `frontend/src/pages/MateriasActividades.tsx`, `frontend/src/pages/Actividades.tsx` (nuevos)
- `frontend/src/router.tsx` (modificado)

### Tests
- Backend: `tests/unit/inc3/test_actividad_evaluativa_periodo_abierto.py`,
  `test_crear_actividad_periodo_abierto_use_case.py` (modificados);
  `test_listar_actividades_use_case.py`, `test_actividades_query_controller.py` (nuevos);
  `tests/integration/inc3/test_actividades_api_integration.py` (modificado);
  `tests/step_defs/inc3/test_us_3_4_2_steps.py` (nuevo)
- Frontend: `frontend/src/lib/actividad-evaluativa-api.test.ts`,
  `frontend/src/router.test.tsx` (modificados)
- `tests/features/inc3/US-3.4.2-listado-materias-actividades-docente.feature` (nuevo)

### Documentación
- `docs/plans/inc3/US-3.4.2-context.md`, `US-3.4.2-plan.md`
- `docs/reports/inc3/US-3.4.2-report.md` (este archivo)
- `quality/reports/inc3/US-3.4.2-quality.json`
- `CHANGELOG.md` (entrada nueva bajo `[Unreleased]`)

---

## Criterios de Aceptación

- [x] `#doc-materias`: tarjeta por materia asignada, navega al listado de actividades
- [x] `#doc-actividades`: tarjeta por actividad con `Badge` de estado y conteos; "+ Nueva
      actividad" navega a `US-3.4.3` (placeholder); cada tarjeta navega al detalle (`US-3.4.4`,
      placeholder)
- [x] Estado calculado puramente derivado (fecha actual + `cerrada_manualmente`), sin persistir
      campo propio

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] Cerrar Issue #171 con los SHAs de los commits de esta US
- [ ] Continuar con `US-3.4.3` (Docente crea una nueva actividad de período abierto) — el
      formulario real que le da valor al campo `titulo`
- [ ] Lado estudiante (`US-3.4.5`→`3.4.6`→`3.4.7`) puede avanzar en paralelo, ambos dependen
      solo de `US-3.4.1`

---

## Lecciones Aprendidas

- ✅ Verificar el dominio contra el prototipo HTML antes de tocar código detectó dos gaps
  reales (`titulo`, conteo de finalizadas) que de otro modo hubiesen aparecido recién en UAT.
- ✅ Decidir `titulo` como campo opcional limitó el blast radius a 0 tests rotos de las
  Iteraciones 1-3 — verificado con la suite completa antes de cerrar la Fase 3.
- ✅ Separar `ActividadesQueryController` desde el diseño evitó repetir el patrón de CRITICAL
  de CBO ya visto 5 veces en el proyecto.
- ✅ Reutilizar `ActividadEvaluativaPeriodoAbierto.reconstruir()` en el gateway de consulta
  mantuvo el nuevo repositorio simple, sin duplicar lógica de reconstrucción.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-30
