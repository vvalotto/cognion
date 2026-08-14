# Reporte de Implementación: US-2.1.9

## Resumen Ejecutivo

- **Historia de Usuario:** US-2.1.9 - Docente ve el listado de materias y da de alta una nueva
- **Puntos estimados:** 5 (ampliado desde 3 por el alcance backend agregado — gap de `US-2.1.8`)
- **Tiempo real:** ~33 min (fases 0-8, ver `docs/plans/inc2/US-2.1.9-plan.md` §Métricas de Tiempo)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-14

---

## Alcance ampliado (gap heredado de US-2.1.8)

El backend nunca expuso `GET /materias` — solo `POST /materias` (`US-2.1.1`). Detectado en
`US-2.1.8` (Fase 2), decisión de Víctor: incorporar el endpoint faltante al alcance de esta
misma US en vez de abrir un ciclo backend separado. El wireframe aprobado (`US-2.0.2`) exige
mostrar la cantidad de preguntas activas por materia, lo que requirió tocar 3 puertos.

---

## Componentes Implementados

### Backend — entities/ports
- ✅ **`MateriaRepositoryPort.listar()`** (`src/banco_preguntas/entities/ports/materia_repository_port.py`)
- ✅ **`BancoRepositoryPort.obtener_por_materia_id()`** (`src/banco_preguntas/entities/ports/banco_repository_port.py`)

### Backend — use_cases
- ✅ **`ListarMateriasUseCase`** (nuevo, `src/banco_preguntas/use_cases/listar_materias.py`)
  - Orquesta materia + banco + conteo de preguntas activas, reutilizando
    `PreguntaRepositoryPort.filtrar()` (`US-2.1.7`) en vez de agregar un método de conteo
    dedicado a ese puerto

### Backend — interface_adapters
- ✅ **`MateriasController`** — inyecta `ListarMateriasUseCase` además de `CrearMateriaUseCase`,
  método nuevo `listar_materias()`
- ✅ **`SQLAlchemyMateriaRepository.listar()`** / **`SQLAlchemyBancoRepository.obtener_por_materia_id()`**

### Backend — frameworks
- ✅ **`GET /materias`** (`src/banco_preguntas/frameworks/api/materias_router.py`) — rol
  `docente`, `response_model=list[MateriaListItemResponse]`
- ✅ **`MateriaListItemResponse`** (`schemas.py`) — id, nombre, banco_id, cantidad_preguntas_activas
- ✅ **`dependencies.py`** — `get_materias_controller` arma ambos use cases

### Frontend
- ✅ **`listarMaterias()`** (`frontend/src/lib/banco-preguntas-api.ts`) — excluida de `US-2.1.8`
  por este mismo gap
- ✅ **`Materias.tsx`** (nuevo) — grilla de materias, tarjeta "Nueva materia" (wireframe §2.1)
- ✅ **`NuevaMateria.tsx`** (nuevo) — formulario de alta, error inline por duplicado, vuelve al
  listado en éxito (wireframe §2.2)
- ✅ **`router.tsx`** — reemplaza los placeholders de `/materias` y `/materias/nueva`

---

## API Endpoints

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/materias` | Lista materias con cantidad de preguntas activas | Rol `docente` |

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint (backend) | 9.96/10 | ≥ 8.0 | ✅ |
| CC máx (backend) | 3 | ≤ 10 | ✅ |
| MI mín (backend) | 55.56 | > 20 | ✅ |
| Coverage (backend, entities/use_cases/interface_adapters) | 100% | ≥ 95% | ✅ |
| oxlint (frontend) | 0 errores | 0 errores | ✅ |
| `tsc --noEmit` (frontend) | 0 errores | 0 errores | ✅ |
| Coverage `Materias.tsx` / `NuevaMateria.tsx` | 100% / 93.33% | ≥ 80% | ✅ |

Fuente: `quality/reports/inc2/US-2.1.9-quality.json`. `frameworks/*` excluido de coverage
backend por configuración del proyecto (`pyproject.toml`). mypy limpio sobre `src/` completo.

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Backend

**Unitarios (7 tests nuevos)**
- `test_listar_materias_use_case.py` (4 tests: sin materias, materia sin preguntas, cuenta
  solo activas, varias materias con su conteo)
- `test_materias_controller.py` (1 test nuevo: delegación de `listar_materias()`)

**Integración (5 tests nuevos)**
- `test_materia_repository_integration.py`: `listar()` incluye persistidas,
  `obtener_por_materia_id()` (existente / inexistente)
- `test_materias_api_integration.py`: `GET /materias` con conteo, 401 sin auth, 403 rol
  insuficiente

**BDD (1 escenario backend)**
- `tests/features/inc2/US-2.1.9-listado-alta-materias.feature` — escenario `GET /materias
  devuelve la cantidad de preguntas activas por materia`, con step defs propios
  (`tests/step_defs/inc2/test_us_2_1_9_steps.py`, usando `@scenario` singular para no
  colisionar con los 3 escenarios frontend del mismo `.feature`)

### Frontend

**Unitarios/Integración (11 tests nuevos, Vitest)**
- `banco-preguntas-api.test.ts` — `listarMaterias()` (mapeo snake_case↔camelCase, lista vacía)
- `Materias.test.tsx` — tarjetas con conteo, navegación al banco, navegación a alta
- `NuevaMateria.test.tsx` — alta exitosa, rechazo por duplicado, cancelar
- `router.test.tsx` — `/materias` y `/materias/nueva` renderizan las pantallas reales (ya no
  el placeholder de `US-2.1.8`)

**Todos los tests pasando:** ✅ 225/225 backend (unit+integration+BDD), 73/73 frontend

---

## Archivos Creados/Modificados

### Código de producción — backend
- `src/banco_preguntas/entities/ports/materia_repository_port.py` (modificado)
- `src/banco_preguntas/entities/ports/banco_repository_port.py` (modificado)
- `src/banco_preguntas/use_cases/listar_materias.py` (nuevo)
- `src/banco_preguntas/interface_adapters/controllers/materias_controller.py` (modificado)
- `src/banco_preguntas/interface_adapters/gateways/materia_repository.py` (modificado)
- `src/banco_preguntas/interface_adapters/gateways/banco_repository.py` (modificado)
- `src/banco_preguntas/frameworks/api/schemas.py` (modificado)
- `src/banco_preguntas/frameworks/api/materias_router.py` (modificado)
- `src/banco_preguntas/frameworks/dependencies.py` (modificado)

### Código de producción — frontend
- `frontend/src/lib/banco-preguntas-api.ts` (modificado)
- `frontend/src/pages/Materias.tsx` (nuevo)
- `frontend/src/pages/NuevaMateria.tsx` (nuevo)
- `frontend/src/router.tsx` (modificado)

### Tests
- `tests/features/inc2/US-2.1.9-listado-alta-materias.feature` (nuevo)
- `tests/step_defs/inc2/test_us_2_1_9_steps.py` (nuevo)
- `tests/unit/inc2/_fakes.py` (modificado — `listar()`, `obtener_por_materia_id()`)
- `tests/unit/inc2/test_listar_materias_use_case.py` (nuevo)
- `tests/unit/inc2/test_materias_controller.py` (modificado)
- `tests/integration/inc2/test_materia_repository_integration.py` (modificado)
- `tests/integration/inc2/test_materias_api_integration.py` (modificado)
- `frontend/src/lib/banco-preguntas-api.test.ts` (modificado)
- `frontend/src/pages/Materias.test.tsx` (nuevo)
- `frontend/src/pages/NuevaMateria.test.tsx` (nuevo)
- `frontend/src/router.test.tsx` (modificado)

### Documentación
- `docs/specs/inc2/US-2.1.9.md` (ampliado con alcance backend)
- `docs/plans/inc2/US-2.1.9-context.md`
- `docs/plans/inc2/US-2.1.9-plan.md`
- `docs/reports/inc2/US-2.1.9-report.md` (este archivo)
- `quality/reports/inc2/US-2.1.9-quality.json` + `-pylint.json` + `-cc.json` + `-mi.json` + `-coverage.json`
- `CHANGELOG.md` (entrada nueva bajo `[Unreleased]`)

---

## Criterios de Aceptación

- [x] `GET /materias` devuelve `id`, `nombre`, `banco_id` y `cantidad_preguntas_activas` por
      materia (rol `docente`)
- [x] Grilla de materias con nombre y cantidad de preguntas activas
- [x] Alta exitosa → vuelve al listado con la materia nueva visible
- [x] Nombre duplicado → error inline en el formulario, sin pantalla propia

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] Cerrar Issue #50 con los SHAs de los commits de esta US
- [ ] `US-2.1.10` — Docente ve y filtra el banco de preguntas de una materia (ya no bloqueada)
- [ ] Con `US-2.1.9` cerrada, la Iteración 1 backend + parte de frontend avanza — evaluar
      cierre de baseline recién al cerrar `US-2.1.10` a `US-2.1.13` (mismo criterio que
      `BL-002`, la Baseline no cierra backend-only)

---

## Lecciones Aprendidas

- ✅ Actualizar el Issue de GitHub junto con la spec (no solo la spec) evitó que la fuente
  pública quedara desalineada con el alcance real acordado.
- ✅ `@scenario` (singular) de pytest-bdd permitió mezclar escenarios backend y frontend en un
  solo `.feature` sin que la colección fallara por los steps frontend inexistentes.
- ✅ Reutilizar `PreguntaRepositoryPort.filtrar()` para el conteo, en vez de agregar un método
  dedicado, mantuvo ese puerto sin ensanchar — mismo criterio que `US-2.1.7`.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-14
