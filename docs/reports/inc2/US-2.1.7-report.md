# Reporte de Implementación: US-2.1.7

## Resumen Ejecutivo

- **Historia de Usuario:** US-2.1.7 - Docente filtra el banco por materia, unidad, tema, dificultad e importancia
- **Puntos estimados:** 3
- **Tiempo real:** ~24 min (fases 0-8, ver `docs/plans/inc2/US-2.1.7-plan.md` §Métricas de Tiempo)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-13

---

## Componentes Implementados

### Entities
- ✅ **`PreguntaRepositoryPort.filtrar()`** (`src/banco_preguntas/entities/ports/pregunta_repository_port.py`)
  - Método abstracto nuevo: `filtrar(banco_id, unidad?, tema?, dificultad?, importancia?)`
  - Solo preguntas con `activa = true`; filtros opcionales y combinables (AND)

### Use Cases
- ✅ **`FiltrarBancoUseCase`** (`src/banco_preguntas/use_cases/filtrar_banco.py`)
  - Valida que el `Banco` exista (`BancoNoExiste` si no), delega el filtro combinado en el
    repositorio de preguntas

### Interface Adapters
- ✅ **`BancosController`** (nuevo, `src/banco_preguntas/interface_adapters/controllers/bancos_controller.py`)
  - Controller separado de `PreguntasController` — decisión de diseño: `PreguntasController`
    ya estaba en CBO=10/10 (el umbral duro de `[tool.designreviewer]`) tras `US-2.1.6`; sumar
    un 5° use case habría repetido el patrón de CRITICAL visto en `US-2.1.2`/`US-2.1.5`/
    `US-2.1.6`. El endpoint además vive bajo el recurso `/bancos/{id}/preguntas`, no
    `/preguntas` — separación natural por recurso, no solo por CBO.
- ✅ **`SQLAlchemyPreguntaRepository.filtrar()`** (`src/banco_preguntas/interface_adapters/gateways/pregunta_repository.py`)
  - `SELECT` con `WHERE` dinámico (`banco_id`, `activa = true` + condiciones opcionales)
  - Mapeo fila→entidad extraído a `_a_entidad()`, reutilizado también por `obtener_por_id()`

### Frameworks
- ✅ **`GET /bancos/{banco_id}/preguntas`** (nuevo, `src/banco_preguntas/frameworks/api/bancos_router.py`)
  - Rol `docente`, filtros opcionales por query params, 404 si `BancoNoExiste`
- ✅ **`dependencies.py`** — `get_bancos_controller` arma `BancosController(FiltrarBancoUseCase(...))`
- ✅ **`src/app.py`** — registro de `bancos_router`

---

## API Endpoints

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/bancos/{banco_id}/preguntas` | Filtrar preguntas activas del banco por unidad/tema/dificultad/importancia | Rol `docente` |

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint | 9.28/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 2 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (mín) | 41.66 | > 20 | ✅ |
| Cobertura de Tests | 99% | ≥ 95% | ✅ |

Fuente: `quality/reports/inc2/US-2.1.7-quality.json`. CodeGuard acotado a los 7 archivos de
`src/` modificados/agregados por esta US: 0 errores, 0 warnings (1 línea E501 corregida en
`filtrar_banco.py`). CC máx real = 2 (clase ABC `PreguntaRepositoryPort`); todo el código de
negocio nuevo tiene CC = 1. Coverage 99%: las 3 líneas sin cubrir son preexistentes en
`materia_repository.py`, no tocadas por esta US (mismo patrón que `US-2.1.6`).

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Tests Unitarios (8 tests nuevos)
- `test_filtrar_banco_use_case.py` (6 tests: filtro combinado dificultad/importancia, sin
  filtros devuelve solo activas, ningún resultado, rechazo por banco inexistente, filtro por
  unidad/tema, no incluye preguntas de otro banco)
- `test_bancos_controller.py` (2 tests: delegación al use case, propagación de filtros)
- `_fakes.py` — `FakePreguntaRepository.filtrar()` agregado (el puerto ABC exige implementarlo)

### Tests de Integración (10 tests nuevos)
- `test_filtrar_banco_integration.py`:
  - `TestSQLAlchemyPreguntaRepositoryFiltrar` (4 tests contra PostgreSQL real: dificultad +
    importancia, sin filtros/solo activas, ningún resultado, unidad + tema)
  - `TestFiltrarPreguntasAPIIntegration` (6 tests HTTP: filtro combinado, sin filtros, ningún
    resultado, banco inexistente → 404, sin autenticación → 401, rol insuficiente → 403)

### Escenarios BDD (3 escenarios)
- `tests/features/inc2/US-2.1.7-filtrar-banco.feature`
  - Filtro combinado por dificultad e importancia
  - Sin filtros adicionales
  - Ningún resultado
- Steps: `tests/step_defs/inc2/test_us_2_1_7_steps.py`

**Todos los tests pasando:** ✅ 258/258 (suite completa del proyecto: unit + integration + step_defs)

---

## Archivos Creados/Modificados

### Código de producción
- `src/banco_preguntas/entities/ports/pregunta_repository_port.py` (modificado)
- `src/banco_preguntas/use_cases/filtrar_banco.py` (nuevo)
- `src/banco_preguntas/interface_adapters/controllers/bancos_controller.py` (nuevo)
- `src/banco_preguntas/interface_adapters/gateways/pregunta_repository.py` (modificado)
- `src/banco_preguntas/frameworks/api/bancos_router.py` (nuevo)
- `src/banco_preguntas/frameworks/dependencies.py` (modificado)
- `src/app.py` (modificado)

### Tests
- `tests/features/inc2/US-2.1.7-filtrar-banco.feature` (nuevo)
- `tests/unit/inc2/test_filtrar_banco_use_case.py` (nuevo)
- `tests/unit/inc2/test_bancos_controller.py` (nuevo)
- `tests/unit/inc2/_fakes.py` (modificado — `FakePreguntaRepository.filtrar()`)
- `tests/integration/inc2/test_filtrar_banco_integration.py` (nuevo)
- `tests/step_defs/inc2/test_us_2_1_7_steps.py` (nuevo)

### Documentación
- `docs/plans/inc2/US-2.1.7-context.md`
- `docs/plans/inc2/US-2.1.7-plan.md`
- `docs/reports/inc2/US-2.1.7-report.md` (este archivo)
- `quality/reports/inc2/US-2.1.7-quality.json`
- `quality/reports/inc2/codeguard/US-2.1.7-codeguard.json`
- `CHANGELOG.md` (entrada nueva bajo `[Unreleased]`)

---

## Criterios de Aceptación

- [x] Filtro combinado por dificultad e importancia devuelve solo las preguntas activas que matchean ambos
- [x] Sin filtros adicionales (solo `materia_id`/`banco_id`) devuelve todas las preguntas activas de la materia
- [x] Sin resultados devuelve lista vacía
- [x] Nunca aparecen preguntas dadas de baja (`activa = false`)
- [x] Filtros opcionales y combinables — cualquier subconjunto de `{unidad, tema, dificultad, importancia}` es válido

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] Cerrar Issue #48 con los SHAs de los commits de esta US
- [ ] `US-2.1.8` — Infraestructura de frontend del Banco de Preguntas (bloquea `US-2.1.9` a `US-2.1.13`)
- [ ] Con `US-2.1.7` cerrada, queda completa toda la Iteración 1 backend (`US-2.1.1` a `US-2.1.7`) — evaluar cierre de baseline según `docs/plans/PLAN-CM.md` §7 una vez cerrado también el frontend (mismo criterio que `BL-002`, la Baseline no cierra backend-only)

---

## Lecciones Aprendidas

- ✅ Detectar en la Fase 2 que `PreguntasController` ya estaba en el umbral de CBO evitó
  repetir el patrón de CRITICAL de las tres US anteriores — crear `BancosController` fue más
  simple que el parche de "tipar como `object`" ya usado tres veces.
- 💡 Extraer `_a_entidad()` en `SQLAlchemyPreguntaRepository` antes de agregar `filtrar()`
  evitó duplicar el mapeo fila→entidad entre ese método y `obtener_por_id()`.
- ⚠️ El coverage con solo tests de integración a nivel HTTP no llegó a las ramas de filtro por
  `unidad`/`tema` en el gateway — hizo falta un test de integración específico del
  repositorio para esas dos ramas del `WHERE` dinámico.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-13
