# Reporte de Implementación: US-2.2.4

## Resumen Ejecutivo

- **Historia de Usuario:** US-2.2.4 - Administrador resetea la contraseña de una cuenta
  (desbloqueo incluido)
- **Puntos estimados:** 2
- **Tiempo real:** ~25 min efectivos (fases 0-9, tracker `.claude/tracking/US-2.2.4-tracking.json`)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-20

---

## Componentes Implementados

### Entities
- ✅ **`PasswordDemasiadoCorta`** (`src/identidad/entities/errors.py`) — error nuevo, INV-ID-11
- ✅ **`PasswordReseteada`**, **`CuentaDesbloqueada`** (`src/identidad/entities/eventos.py`) —
  eventos nuevos; `CuentaDesbloqueada` mismo shape que `CuentaBloqueada` (`US-2.2.1`)
- ✅ **`Usuario.validar_password_nueva()`** (`src/identidad/entities/usuario.py`) — staticmethod,
  primera vez que INV-ID-11 se enforza del lado del dominio (antes solo vía Pydantic
  `min_length=8` en `CrearUsuarioRequest`); queda reutilizable para `US-2.2.5`
- ✅ **`usuario.resetear_password()`** (`src/identidad/entities/usuario.py`) — mutación de
  estado pura (hash + desbloqueo + reseteo de ambos contadores), devuelve si estaba bloqueada

### Use Case
- ✅ **`ResetearPasswordUseCase`** (`src/identidad/use_cases/resetear_password.py`) — orden:
  `obtener_por_id` (404) → `validar_password_nueva` (422) → hash → `resetear_password` en la
  entidad → `actualizar` en el repositorio; arma `PasswordReseteada` siempre y
  `CuentaDesbloqueada` solo si la cuenta estaba bloqueada

### Interface Adapters
- ✅ **`CuentasController.resetear_password()`**
  (`src/identidad/interface_adapters/controllers/cuentas_controller.py`) — tercer método/use
  case inyectado (`ListarCuentasUseCase`/`ObtenerCuentaUseCase` de `US-2.2.2`/`US-2.2.3` +
  `ResetearPasswordUseCase` nuevo); devuelve solo la entidad actualizada, no los eventos

### Frameworks
- ✅ **`ResetearPasswordRequest`** (`src/identidad/frameworks/api/schemas.py`) — schema nuevo,
  `password_nueva: str = Field(..., min_length=8)`
- ✅ **`POST /usuarios/{usuario_id}/resetear-password`**
  (`src/identidad/frameworks/api/cuentas_router.py`) — rol `administrador`;
  `administrador_id` resuelto del JWT (`JWTPayload.usuario_id` vía `require_administrador`
  inyectado como parámetro, no del body); 404 si `UsuarioNoExiste`, 422 si
  `PasswordDemasiadoCorta`; responde `CuentaDetalleResponse` (reusa `US-2.2.3`, factorizado a
  `_a_detalle_response()` para no duplicar con `obtener_cuenta`)
- ✅ **`dependencies.py`** — `get_cuentas_controller` arma también
  `ResetearPasswordUseCase(usuario_repo, get_password_hasher())`

---

## API Endpoints

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| POST | `/usuarios/{usuario_id}/resetear-password` | Resetea contraseña; desbloquea si corresponde | Rol `administrador` |

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint | 9.95/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 7 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (mín) | 48.58 | > 20 | ✅ |
| Cobertura de Tests | 99% | ≥ 95% | ✅ |
| codeguard (Security/PEP8/Complexity) | 0 errors, 0 warnings | 0 errors | ✅ |

Fuente: `quality/reports/inc2/US-2.2.4-quality.json`. CC/MI medidos sobre `src/identidad`
completo — ambos son deuda preexistente sin relación con el código de esta US (no en los
archivos modificados). `resetear_password.py`: 100% coverage.

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Tests Unitarios (14 tests nuevos)
- `tests/unit/inc1/test_usuario.py` (10 tests nuevos: `validar_password_nueva` — acepta 8/larga,
  rechaza corta/vacía; `resetear_password` — actualiza hash, resetea bloqueada y ambos
  contadores, devuelve `True`/`False` según estado previo)
- `tests/unit/inc1/test_resetear_password_use_case.py` (5 tests: actualiza hash, cuenta
  bloqueada emite ambos eventos, cuenta activa no emite `CuentaDesbloqueada`, `UsuarioNoExiste`,
  `PasswordDemasiadoCorta` sin modificar el usuario)
- `tests/unit/inc1/test_cuentas_controller.py` (1 test nuevo: `resetear_password` delega y
  devuelve la entidad actualizada; constructor del controller actualizado con la 3ra dependencia)

### Tests de Integración (5 tests nuevos)
- `tests/integration/inc1/test_usuarios_api_integration.py` — `TestResetearPasswordAPIIntegration`
  (cuenta bloqueada se desbloquea, password reseteada habilita login real vía `/identidad/login`,
  cuenta activa no queda bloqueada, password corta → 422, cuenta inexistente → 404, sin rol
  administrador → 401)

### Escenarios BDD (3 escenarios)
- `tests/features/inc2/US-2.2.4-resetear-password.feature` +
  `tests/step_defs/inc2/test_us_2_2_4_steps.py` — los 3 criterios de aceptación de la spec, 1:1

**Todos los tests pasando:** ✅ 329/329 (unit + integration + step_defs, suite completa)

---

## Archivos Creados/Modificados

### Código de producción
- `src/identidad/entities/errors.py`
- `src/identidad/entities/eventos.py`
- `src/identidad/entities/usuario.py`
- `src/identidad/use_cases/resetear_password.py` (nuevo)
- `src/identidad/interface_adapters/controllers/cuentas_controller.py`
- `src/identidad/frameworks/api/schemas.py`
- `src/identidad/frameworks/api/cuentas_router.py`
- `src/identidad/frameworks/dependencies.py`

### Tests
- `tests/unit/inc1/test_usuario.py` (extendido)
- `tests/unit/inc1/test_resetear_password_use_case.py` (nuevo)
- `tests/unit/inc1/test_cuentas_controller.py` (extendido)
- `tests/integration/inc1/test_usuarios_api_integration.py` (extendido)
- `tests/features/inc2/US-2.2.4-resetear-password.feature` (nuevo)
- `tests/step_defs/inc2/test_us_2_2_4_steps.py` (nuevo)

### Documentación
- `docs/plans/inc2/US-2.2.4-context.md`
- `docs/plans/inc2/US-2.2.4-plan.md`
- `docs/reports/inc2/US-2.2.4-report.md` (este archivo)
- `quality/reports/inc2/US-2.2.4-quality.json`
- `quality/reports/inc2/US-2.2.4-codeguard.json`
- `CHANGELOG.md` (entrada nueva bajo `[Unreleased]`)

---

## Criterios de Aceptación

- [x] Reseteo de cuenta bloqueada: actualiza `password_hash`, `bloqueada → false`, ambos
  contadores a 0, emite `PasswordReseteada` y `CuentaDesbloqueada`
- [x] Reseteo de cuenta activa: actualiza `password_hash`, emite solo `PasswordReseteada`
- [x] Rechazo por contraseña demasiado corta: `PasswordDemasiadoCorta`, sin modificar el usuario

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] `US-2.2.5` — Usuario autenticado cambia su propia contraseña (reutiliza
  `Usuario.validar_password_nueva()` de esta US)
- [ ] `US-2.2.6` — siguiente US de la Iteración 2 (`docs/specs/inc2/`)
- [ ] `US-2.2.7` — Frontend de reseteo de contraseña (consume este endpoint)

---

## Lecciones Aprendidas

- ✅ Separar la validación de dominio (`Usuario.validar_password_nueva`, sobre texto plano) de
  la mutación de estado (`usuario.resetear_password`, sobre el hash ya calculado) evitó que la
  entidad necesitara depender del hasher, manteniendo `entities/` sin dependencias externas.
- ✅ El CBO de `CuentasController` no llegó a CRITICAL al pasar de 2 a 3 métodos — cada uno
  delega en un único use case sin acoplar tipos nuevos entre sí; la contingencia de separar
  command/query documentada en el plan no hizo falta.
- 💡 Factorizar `_a_detalle_response()` en el router evitó duplicar el mapeo `Usuario →
  CuentaDetalleResponse` entre `obtener_cuenta` y el nuevo `resetear_password`.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-20
