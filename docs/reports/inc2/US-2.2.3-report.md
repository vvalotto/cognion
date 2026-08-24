# Reporte de Implementación: US-2.2.3

## Resumen Ejecutivo

- **Historia de Usuario:** US-2.2.3 - Administrador ve el detalle de una cuenta
- **Puntos estimados:** 2
- **Tiempo real:** ~24 min (fases 0-7, ver `docs/plans/inc2/US-2.2.3-plan.md` §Métricas de Tiempo)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-19

---

## Componentes Implementados

### Entities
- ✅ **`Usuario.creado_en`** (`src/identidad/entities/usuario.py`) — campo nuevo,
  `field(default_factory=_ahora)`, se fija al construir la entidad (`crear()`/
  `crear_estudiante()`). Decisión de Víctor confirmada en esta sesión: agregar el campo ahora
  en vez de excluirlo del alcance (era un gap de la spec — el campo no existía).
- ✅ **`UsuarioNoExiste`** (`src/identidad/entities/errors.py`) — error nuevo

### Use Case
- ✅ **`ObtenerCuentaUseCase`** (`src/identidad/use_cases/obtener_cuenta.py`) — reutiliza
  `UsuarioRepositoryPort.obtener_por_id()` ya existente, lanza `UsuarioNoExiste` si no hay
  match

### Interface Adapters
- ✅ **`CuentasController.obtener_cuenta()`** (`src/identidad/interface_adapters/controllers/cuentas_controller.py`)
  — segundo método/use case inyectado (`ListarCuentasUseCase` de `US-2.2.2` +
  `ObtenerCuentaUseCase` nuevo)

### Frameworks
- ✅ **`CuentaDetalleResponse`** (`src/identidad/frameworks/api/schemas.py`) — schema nuevo
  con `creado_en` y `comision_id: UUID | None`
- ✅ **`GET /usuarios/{usuario_id}`** (`src/identidad/frameworks/api/cuentas_router.py`) —
  rol `administrador`, 404 si `UsuarioNoExiste`, arma `comision_id` desde
  `isinstance(usuario.perfil, Estudiante)`
- ✅ **`dependencies.py`** — `get_cuentas_controller` arma también `ObtenerCuentaUseCase`
- ✅ **`UsuarioModel.creado_en`** (`src/identidad/frameworks/db/models.py`) — columna nueva
- ✅ Migración Alembic `92b42288ef96_usuario_creado_en.py` — `nullable=False` con
  `server_default=func.now()` (backfill de filas existentes), aplicada localmente
- ✅ **`SQLAlchemyUsuarioRepository`** — `guardar()`/`_armar_usuario()` wirean `creado_en`
  explícito entre entidad y fila

---

## API Endpoints

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/usuarios/{usuario_id}` | Detalle completo de una cuenta puntual | Rol `administrador` |

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint | 9.76/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 7 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (mín) | 48.87 | > 20 | ✅ |
| Cobertura de Tests | 99% | ≥ 95% | ✅ |
| Pre-push gate (CBOAnalyzer y resto) | 0 CRITICAL | 0 CRITICAL | ✅ |

Fuente: `quality/reports/inc2/US-2.2.3-quality.json`. A diferencia de `US-2.2.2`, no se
repitió el CBO CRITICAL — sumar un segundo método a `CuentasController` (1→2) y reutilizar
`SQLAlchemyUsuarioRepository.obtener_por_id()` en vez de acoplar tipos nuevos al gateway
evitó el problema desde el diseño.

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Tests Unitarios (5 tests nuevos)
- `tests/unit/inc1/test_obtener_cuenta_use_case.py` (3 tests: detalle Docente, detalle
  Estudiante con `comision_id`, `UsuarioNoExiste`)
- `tests/unit/inc1/test_cuentas_controller.py` (1 test nuevo: `test_obtener_cuenta_delega_en_el_use_case`)
- 100% coverage en `entities/`, `use_cases/` y `controllers/` nuevos/modificados

### Tests de Integración (4 tests nuevos)
- `tests/integration/inc1/test_usuarios_api_integration.py` — `TestObtenerCuentaAPIIntegration`
  (detalle de Docente, detalle de Estudiante con `comision_id` real vía Comisión creada en
  DB, 404 en cuenta inexistente, 401 sin rol administrador)
- Fix en `test_usuario_repository_integration.py`: el test que construye `UsuarioModel`
  directamente (fila "huérfana" sin perfil) necesitó pasar `creado_en` explícito tras
  volverse `nullable=False`

### Escenarios BDD (3 escenarios)
- `tests/features/inc2/US-2.2.3-detalle-cuenta.feature` +
  `tests/step_defs/inc2/test_us_2_2_3_steps.py` — los 3 criterios de aceptación de la spec, 1:1

**Todos los tests pasando:** ✅ 305/305 (unit + integration + step_defs, suite completa)

---

## Archivos Creados/Modificados

### Código de producción
- `src/identidad/entities/usuario.py`
- `src/identidad/entities/errors.py`
- `src/identidad/use_cases/obtener_cuenta.py`
- `src/identidad/interface_adapters/controllers/cuentas_controller.py`
- `src/identidad/frameworks/api/schemas.py`
- `src/identidad/frameworks/api/cuentas_router.py`
- `src/identidad/frameworks/dependencies.py`
- `src/identidad/frameworks/db/models.py`
- `src/identidad/interface_adapters/gateways/usuario_repository.py`
- `migrations/versions/92b42288ef96_usuario_creado_en.py`

### Tests
- `tests/unit/inc1/test_obtener_cuenta_use_case.py`
- `tests/unit/inc1/test_cuentas_controller.py` (extendido)
- `tests/integration/inc1/test_usuarios_api_integration.py` (extendido)
- `tests/integration/inc1/test_usuario_repository_integration.py` (fix `creado_en`)
- `tests/features/inc2/US-2.2.3-detalle-cuenta.feature`
- `tests/step_defs/inc2/test_us_2_2_3_steps.py`

### Documentación
- `docs/plans/inc2/US-2.2.3-context.md`
- `docs/plans/inc2/US-2.2.3-plan.md`
- `docs/reports/inc2/US-2.2.3-report.md` (este archivo)
- `quality/reports/inc2/US-2.2.3-quality.json`

---

## Criterios de Aceptación

- [x] Detalle de un Estudiante incluye `comision_id`
- [x] Detalle de un Docente tiene `comision_id` en `null`
- [x] Cuenta inexistente rechaza con `UsuarioNoExiste` (404)

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] `US-2.2.4` — Administrador resetea la contraseña de una cuenta (única forma de
  desbloquear); cierra el backend de RF-03
- [ ] `US-2.2.5` — Usuario autenticado cambia su propia contraseña (RF-19, backend restante)
- [ ] `US-2.2.7` — Frontend del detalle de cuenta (consume este endpoint)

---

## Lecciones Aprendidas

- ✅ El pre-push gate no repitió el CBO CRITICAL de `US-2.2.2` — separar por responsabilidad
  desde el diseño (reutilizar `obtener_por_id()` en vez de acoplar tipos nuevos al gateway)
  evitó el problema en vez de tener que corregirlo después.
- ⚠️ Agregar una columna `nullable=False` rompe cualquier test que construya el modelo ORM
  directamente sin pasar por la entidad/gateway — revisar esos tests cada vez.
- 💡 Fijar campos de auditoría (`creado_en`) en la entidad de dominio, no solo con
  `server_default` en la columna, mantiene entidad y fila consistentes.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-19
