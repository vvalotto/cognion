# Reporte de Implementación: US-2.2.2

## Resumen Ejecutivo

- **Historia de Usuario:** US-2.2.2 - Administrador ve el listado de cuentas, filtra por rol/estado/búsqueda
- **Puntos estimados:** 3
- **Tiempo real:** ~29 min (fases 0-7, ver `docs/plans/inc2/US-2.2.2-plan.md` §Métricas de Tiempo)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-19

---

## Componentes Implementados

> **Nota:** el diseño original (Fase 2, aprobado) agregaba `listar()` directo a
> `UsuarioRepositoryPort`/`SQLAlchemyUsuarioRepository`. El pre-push gate (`CBOAnalyzer`)
> bloqueó ese diseño con CRITICAL (CBO=11/10, verificado contra `develop` que la clase estaba
> en umbral antes del cambio) — mismo patrón recurrente que `US-2.1.2`/`US-2.1.5`/`US-2.1.6`.
> Se resolvió separando la consulta en un puerto y gateway propios. Lo que sigue documenta el
> **diseño final entregado**.

### Puerto y Gateway
- ✅ **`CuentaQueryPort`** (`src/identidad/entities/ports/cuenta_query_port.py`) — puerto nuevo,
  separado de `UsuarioRepositoryPort` (altas/persistencia) por responsabilidad command/query,
  mismo criterio que separa `CuentasController` de `UsuariosController`, extendido a
  persistencia. Único método: `listar(rol, estado, busqueda) -> list[Usuario]`
- ✅ **`SQLAlchemyCuentaQueryRepository`** (`src/identidad/interface_adapters/gateways/cuenta_query_repository.py`)
  — `SELECT` con `join()` condicional a la tabla de perfil según `rol`, filtro `bloqueada`
  según `estado` (`activa`/`bloqueada`), `ILIKE` combinado con `or_()` contra `nombre`/`email`
  según `busqueda`; delega el armado de cada `Usuario` en
  `SQLAlchemyUsuarioRepository.obtener_por_id()` (API pública, sin acceder a métodos privados
  de otra instancia) — `UsuarioRepositoryPort`/`SQLAlchemyUsuarioRepository` quedan sin cambios
  respecto a `develop`

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
| Pylint | 9.78/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 7 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (mín) | 53.50 | > 20 | ✅ |
| Cobertura de Tests | 99% | ≥ 95% | ✅ |
| Pre-push gate (CBOAnalyzer y resto) | 0 CRITICAL | 0 CRITICAL | ✅ |

Fuente: `quality/reports/inc2/US-2.2.2-quality.json`. Única línea genuinamente no cubierta:
el guard defensivo preexistente de `actualizar()` (`US-2.2.1`). Las líneas del bucle de
`SQLAlchemyCuentaQueryRepository.listar()` aparecen como no cubiertas en el reporte de
`coverage.py` pese a ejecutarse correctamente — verificado con una llamada real end-to-end —
artefacto de instrumentación documentado en el quality report, no un gap de tests.

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
- `src/identidad/entities/ports/cuenta_query_port.py`
- `src/identidad/interface_adapters/gateways/cuenta_query_repository.py`
- `src/identidad/use_cases/listar_cuentas.py`
- `src/identidad/interface_adapters/controllers/cuentas_controller.py`
- `src/identidad/frameworks/api/schemas.py`
- `src/identidad/frameworks/api/cuentas_router.py`
- `src/identidad/frameworks/dependencies.py`
- `src/app.py`

### Tests
- `tests/unit/inc1/_fakes.py` (agrega `FakeCuentaQueryRepository`)
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
- 🔴 Agregar un método nuevo a un repositorio ya cerca del umbral de CBO lo hace CRITICAL en
  el pre-push gate, no en Fase 7 (que no mide acoplamiento). El fix consistente con el resto
  del proyecto es separar en un puerto/gateway propio por responsabilidad (command/query),
  no forzar el método en la clase existente — y verificar el estado "antes" contra `develop`
  para confirmar que el cambio propio es la causa antes de rediseñar.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-19
