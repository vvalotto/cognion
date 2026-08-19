# Reporte de Implementación: US-2.2.2

## Resumen Ejecutivo

- **Historia de Usuario:** US-2.2.2 - Administrador ve el listado de cuentas, filtra por rol/estado/búsqueda
- **Puntos estimados:** 3
- **Tiempo real:** ~29 min (fases 0-7, ver `docs/plans/inc2/US-2.2.2-plan.md` §Métricas de Tiempo)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-19

---

## Componentes Implementados

### Puerto y Gateway
- ✅ **`UsuarioRepositoryPort.listar()`** (`src/identidad/entities/ports/usuario_repository_port.py`)
  — nuevo método abstracto `listar(rol, estado, busqueda) -> list[Usuario]`
- ✅ **`SQLAlchemyUsuarioRepository.listar()`** (`src/identidad/interface_adapters/gateways/usuario_repository.py`)
  — `SELECT` con `join()` condicional a la tabla de perfil según `rol`, filtro `bloqueada`
  según `estado` (`activa`/`bloqueada`), `ILIKE` combinado con `or_()` contra `nombre`/`email`
  según `busqueda`; cada fila se resuelve con `_armar_usuario()` ya existente

### Use Case
- ✅ **`ListarCuentasUseCase`** (`src/identidad/use_cases/listar_cuentas.py`) — delega directo
  en el repositorio, sin lógica adicional (query pura, sin invariantes de dominio)

### Interface Adapters
- ✅ **`CuentasController`** (`src/identidad/interface_adapters/controllers/cuentas_controller.py`)
  — controller nuevo, separado de `UsuariosController` (creación) por responsabilidad
  command/query; base para que `US-2.2.3`/`US-2.2.4` sumen métodos

### Frameworks
- ✅ **`CuentaResponse`** (`src/identidad/frameworks/api/schemas.py`) — schema nuevo con
  `bloqueada`, distinto de `UsuarioResponse`
- ✅ **`GET /usuarios`** (`src/identidad/frameworks/api/cuentas_router.py`) — rol
  `administrador`, query params `rol`/`estado`/`busqueda` opcionales
- ✅ **`dependencies.py`** — `get_cuentas_controller` nuevo
- ✅ **`app.py`** — `cuentas_router` registrado

---

## API Endpoints

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/usuarios?rol=&estado=&busqueda=` | Listado de cuentas filtrado (AND) | Rol `administrador` |

`GET`/`POST` conviven en el mismo path `/usuarios` desde dos routers distintos —
verificado sin conflicto vía el schema OpenAPI.

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint | 9.71/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 8 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (mín) | 50.41 | > 20 | ✅ |
| Cobertura de Tests | 99% | ≥ 95% | ✅ |

Fuente: `quality/reports/inc2/US-2.2.2-quality.json`. Única línea genuinamente no cubierta:
el guard defensivo preexistente de `actualizar()` (`US-2.2.1`). Las líneas del bucle de
`listar()` aparecen como no cubiertas en el reporte de `coverage.py` pese a ejecutarse
correctamente — verificado con una llamada real end-to-end — artefacto de instrumentación
documentado en el quality report, no un gap de tests.

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Tests Unitarios (6 tests nuevos)
- `tests/unit/inc1/test_listar_cuentas_use_case.py` (5 tests: sin filtros, filtro combinado
  rol+estado, búsqueda parcial, búsqueda case-insensitive, sin resultados)
- `tests/unit/inc1/test_cuentas_controller.py` (1 test: delegación al use case)
- 100% coverage en `entities/`, `use_cases/` y `controllers/` nuevos

### Tests de Integración (4 tests nuevos)
- `tests/integration/inc1/test_usuarios_api_integration.py` — `TestListarCuentasAPIIntegration`
  (listado sin filtros, filtro por rol+búsqueda, filtro por estado activa, 401 sin auth)

### Escenarios BDD (3 escenarios)
- `tests/features/inc2/US-2.2.2-listado-cuentas.feature` +
  `tests/step_defs/inc2/test_us_2_2_2_steps.py` — los 3 criterios de aceptación de la spec, 1:1

**Todos los tests pasando:** ✅ 294/294 (unit + integration + step_defs, suite completa)

---

## Archivos Creados/Modificados

### Código de producción
- `src/identidad/entities/ports/usuario_repository_port.py`
- `src/identidad/interface_adapters/gateways/usuario_repository.py`
- `src/identidad/use_cases/listar_cuentas.py`
- `src/identidad/interface_adapters/controllers/cuentas_controller.py`
- `src/identidad/frameworks/api/schemas.py`
- `src/identidad/frameworks/api/cuentas_router.py`
- `src/identidad/frameworks/dependencies.py`
- `src/app.py`

### Tests
- `tests/unit/inc1/_fakes.py` (agrega `listar()` a `FakeUsuarioRepository`)
- `tests/unit/inc1/test_listar_cuentas_use_case.py`
- `tests/unit/inc1/test_cuentas_controller.py`
- `tests/integration/inc1/test_usuarios_api_integration.py`
- `tests/features/inc2/US-2.2.2-listado-cuentas.feature`
- `tests/step_defs/inc2/test_us_2_2_2_steps.py`

### Documentación
- `docs/plans/inc2/US-2.2.2-context.md`
- `docs/plans/inc2/US-2.2.2-plan.md`
- `docs/reports/inc2/US-2.2.2-report.md` (este archivo)
- `quality/reports/inc2/US-2.2.2-quality.json`

---

## Criterios de Aceptación

- [x] Listado sin filtros devuelve todas las cuentas
- [x] Filtro combinado por rol y estado (solo Estudiantes con `bloqueada = true`)
- [x] Búsqueda por email parcial (case-insensitive) encuentra la cuenta

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] `US-2.2.3` — Administrador ve el detalle de una cuenta (suma método a `CuentasController`)
- [ ] `US-2.2.4` — Administrador resetea la contraseña de una cuenta
- [ ] `US-2.2.6` — Frontend del listado de cuentas (consume este endpoint)

---

## Lecciones Aprendidas

- 💡 FastAPI permite routers distintos compartiendo `prefix` sin conflicto de rutas mientras
  no colisione método+path — no hace falta forzar un único router por resource REST.
- ⚠️ `coverage.py` no siempre traza el cuerpo de un `for` async justo después de un `await`
  de SQLAlchemy — verificar funcionalmente antes de asumir un gap real de tests.
- ✅ La separación `CuentasController`/`UsuariosController` (queries vs. creación) sobre el
  mismo aggregate deja una base limpia para las próximas dos US de esta iteración.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-19
