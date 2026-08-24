# Reporte de Implementación: US-2.2.5

## Resumen Ejecutivo

- **Historia de Usuario:** US-2.2.5 - Usuario autenticado cambia su propia contraseña
- **Puntos estimados:** 2
- **Tiempo real:** ~53 min efectivos (fases 0-9, tracker `.claude/tracking/US-2.2.5-tracking.json`)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-20

---

## Componentes Implementados

### Entities
- ✅ **`PasswordActualIncorrecta`** (`src/identidad/entities/errors.py`) — error nuevo, mismo
  shape que `CredencialesInvalidas` (atributo `evento_cuenta_bloqueada` completado si el
  fallo es el 3er consecutivo)
- ✅ **`PasswordCambiada`** (`src/identidad/entities/eventos.py`) — evento nuevo;
  `CuentaBloqueada` se reutiliza tal cual (`US-2.2.1`)
- ✅ **`Usuario.cambiar_password()`** (`src/identidad/entities/usuario.py`) — mutación de
  estado pura, fija el hash nuevo y resetea `intentos_fallidos_password` a 0, sin tocar
  `bloqueada` ni `intentos_fallidos_login`
- ✅ **`Usuario.registrar_fallo_cambio_password()`** (`src/identidad/entities/usuario.py`) —
  incrementa el contador propio, bloquea al 3er fallo consecutivo (INV-ID-10), devuelve si
  este fallo bloqueó la cuenta

### Use Case
- ✅ **`CambiarPasswordUseCase`** (`src/identidad/use_cases/cambiar_password.py`, nuevo) —
  orden: `obtener_por_id` (404) → si `bloqueada`, `CuentaBloqueadaError` sin verificar nada →
  si `password_actual` no verifica, `registrar_fallo_cambio_password()` +
  `PasswordActualIncorrecta` (con `evento_cuenta_bloqueada` si corresponde) →
  `Usuario.validar_password_nueva()` (`US-2.2.4`) → hash → `cambiar_password()` → devuelve
  `PasswordCambiada`

### Interface Adapters
- ✅ **`PerfilController`** (`src/identidad/interface_adapters/controllers/perfil_controller.py`,
  nuevo) — controller separado de `CuentasController`, por actor (self-service vs.
  administración), no solo command/query como `US-2.2.2` — evita repetir el patrón recurrente
  de CRITICAL de CBO de `US-2.1.2`/`.5`/`.6`/`US-2.2.2` al no forzar un 4° use case en
  `CuentasController`

### Frameworks
- ✅ **`CambiarPasswordRequest`** (`src/identidad/frameworks/api/schemas.py`) — schema nuevo,
  `password_actual: str`, `password_nueva: str = Field(..., min_length=8)`
- ✅ **`PUT /usuarios/me/password`** (`src/identidad/frameworks/api/perfil_router.py`, nuevo) —
  cualquier rol autenticado (`get_current_user`, sin `require_rol`); `usuario_id` resuelto del
  JWT; 401 si `PasswordActualIncorrecta`, 403 si `CuentaBloqueadaError`, 422 si
  `PasswordDemasiadoCorta`; 204 en éxito (sin body — a diferencia de `resetear_password`, no
  hay detalle que un Administrador necesite ver)
- ✅ **`dependencies.py`** — `get_perfil_controller` arma
  `CambiarPasswordUseCase(usuario_repo, get_password_hasher())`
- ✅ **`src/app.py`** — registra `perfil_router`

---

## API Endpoints

| Método | Ruta | Descripción | Auth |
|--------|------|--------------|------|
| PUT | `/usuarios/me/password` | Cambia la propia contraseña, bloqueo al 3er fallo | Cualquier rol autenticado |

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint | 9.80/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 7 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (mín) | 48.17 | > 20 | ✅ |
| Cobertura de Tests | 99% | ≥ 95% | ✅ |
| codeguard (Security/PEP8/Complexity) | 0 errors reales, 0 warnings | 0 errors | ✅ |

Fuente: `quality/reports/inc2/US-2.2.5-quality.json`. CC/MI medidos sobre `src/identidad`
completo — ambos son deuda preexistente sin relación con el código de esta US (no en los
archivos modificados). `cambiar_password.py`, métodos nuevos de `usuario.py` y
`perfil_controller.py`: 100% coverage.

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Tests Unitarios (14 tests nuevos)
- `tests/unit/inc1/test_usuario.py` (6 tests nuevos: `cambiar_password` — actualiza hash,
  resetea el contador propio, no toca `bloqueada`/`intentos_fallidos_login`;
  `registrar_fallo_cambio_password` — incrementa, no bloquea antes del 3er fallo, bloquea y
  devuelve `True` al 3er fallo)
- `tests/unit/inc1/test_cambiar_password_use_case.py` (7 tests: cambio exitoso,
  `UsuarioNoExiste`, cuenta ya bloqueada sin verificar password, fallo sin llegar al límite,
  3er fallo bloquea, `PasswordDemasiadoCorta` sin modificar el usuario)
- `tests/unit/inc1/test_perfil_controller.py` (1 test nuevo: `cambiar_password` delega en el
  use case)

### Tests de Integración (7 tests nuevos)
- `tests/integration/inc1/test_perfil_api_integration.py` (nuevo) —
  `TestCambiarPasswordAPIIntegration` (cambio exitoso → 204, password cambiada habilita login
  real vía `/identidad/login`, password actual incorrecta → 401, 3er fallo consecutivo
  bloquea y devuelve 401, cuenta ya bloqueada → 403, password nueva corta → 422, sin
  autenticación → 401)

### Escenarios BDD (5 escenarios)
- `tests/features/inc2/US-2.2.5-cambiar-password.feature` +
  `tests/step_defs/inc2/test_us_2_2_5_steps.py` — los 5 criterios de aceptación de la spec, 1:1

**Todos los tests pasando:** ✅ 354/354 (unit + integration + step_defs, suite completa)

---

## Archivos Creados/Modificados

### Código de producción
- `src/identidad/entities/errors.py`
- `src/identidad/entities/eventos.py`
- `src/identidad/entities/usuario.py`
- `src/identidad/use_cases/cambiar_password.py` (nuevo)
- `src/identidad/interface_adapters/controllers/perfil_controller.py` (nuevo)
- `src/identidad/frameworks/api/schemas.py`
- `src/identidad/frameworks/api/perfil_router.py` (nuevo)
- `src/identidad/frameworks/dependencies.py`
- `src/app.py`

### Tests
- `tests/unit/inc1/test_usuario.py` (extendido)
- `tests/unit/inc1/test_cambiar_password_use_case.py` (nuevo)
- `tests/unit/inc1/test_perfil_controller.py` (nuevo)
- `tests/integration/inc1/test_perfil_api_integration.py` (nuevo)
- `tests/features/inc2/US-2.2.5-cambiar-password.feature` (nuevo)
- `tests/step_defs/inc2/test_us_2_2_5_steps.py` (nuevo)

### Documentación
- `docs/plans/inc2/US-2.2.5-context.md`
- `docs/plans/inc2/US-2.2.5-plan.md`
- `docs/reports/inc2/US-2.2.5-report.md` (este archivo)
- `quality/reports/inc2/US-2.2.5-quality.json`
- `quality/reports/codeguard/US-2.2.5-codeguard.json`
- `CHANGELOG.md` (entrada nueva bajo `[Unreleased]`)

---

## Criterios de Aceptación

- [x] Cambio exitoso: actualiza `password_hash`, `intentos_fallidos_password` vuelve a 0,
  emite `PasswordCambiada`, el JWT en curso sigue siendo válido (ADR-013)
- [x] Contraseña actual incorrecta sin llegar al límite: contador +1, rechaza con
  `PasswordActualIncorrecta`
- [x] Tercer fallo consecutivo: contador a 3, `bloqueada` a true, emite `CuentaBloqueada`
- [x] Rechazo por contraseña nueva demasiado corta: `PasswordDemasiadoCorta`
- [x] Cuenta ya bloqueada: rechaza con `CuentaBloqueadaError` sin verificar `password_actual`

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] `US-2.2.6` — Administrador ve y filtra el listado de cuentas (UI), primera US frontend
  de la Iteración 2 (Issue #101)
- [ ] `US-2.2.7` — Administrador ve el detalle de una cuenta y resetea/desbloquea (UI, consume
  `US-2.2.3`/`US-2.2.4`, Issue #102)
- [ ] `US-2.2.8` — Cualquier usuario cambia su propia contraseña (UI, consume esta US, Issue #103)
- [ ] `US-2.2.9` — Login refleja el estado de cuenta bloqueada (UI, Issue #104)

Cierra el backend completo de la Iteración 2 (`US-2.2.1` a `US-2.2.5`). Sigue el frontend
(`US-2.2.6` a `US-2.2.9`) antes de evaluar UAT y cierre de baseline (`BL-003`).

---

## Lecciones Aprendidas

- ✅ Separar el controller por actor (self-service vs. administración) desde el diseño en
  Fase 2 — no solo por command/query como `US-2.2.2` — evitó de nuevo el patrón recurrente de
  CRITICAL de CBO que afectó a `US-2.1.2`/`.5`/`.6`/`US-2.2.2`.
- ⚠️ `UsuarioRepositoryPort.guardar()` no persiste `bloqueada` ni los contadores de intentos —
  solo `password_hash`, `nombre`, `email`, `creado_en` y el perfil. Un test que arma
  `Usuario.crear()` + `usuario.bloqueada = True` + `guardar()` para simular una cuenta ya
  bloqueada queda con una aserción trivialmente verdadera si no se llama también a
  `actualizar()` después — se detectó al escribir el test de integración de "cuenta ya
  bloqueada" de esta US (falló con 204 en vez de 403 hasta corregirlo). El mismo patrón débil
  está presente en el test equivalente de `US-2.2.4`
  (`test_reseteo_de_cuenta_bloqueada_la_desbloquea`) sin que fallara ahí porque su aserción no
  depende de que el bloqueo se haya persistido — queda como deuda de test, no de producción.
- 💡 Encapsular el contador de fallos en un método de la entidad
  (`registrar_fallo_cambio_password()`) en vez de mutarlo directo en el use case (como hace
  `IniciarSesionUseCase` con `intentos_fallidos_login`) deja el use case más corto y el
  comportamiento de bloqueo testeable de forma aislada — dos estilos conviven en el BC, ambos
  válidos según si el efecto es reutilizable fuera del flujo puntual.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-20
