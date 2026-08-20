# Plan de Implementación: US-2.2.5 - Usuario autenticado cambia su propia contraseña

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** identidad

## Decisión de diseño: controller nuevo, no `CuentasController`

`CuentasController` ya tiene 3 use cases inyectados (`ListarCuentasUseCase`,
`ObtenerCuentaUseCase`, `ResetearPasswordUseCase`, todos de administración — actor
Administrador). `CambiarPassword` es self-service (actor: cualquier Usuario autenticado sobre
su propia cuenta) — actor y responsabilidad distintos, mismo criterio de separación
command/query/actor usado en `US-2.2.2` (`CuentaQueryPort` separado) y `US-2.1.7`
(`BancosController` separado de `PreguntasController`). Se crea `PerfilController` nuevo, con
un único método por ahora — evita repetir el patrón recurrente de CRITICAL de CBO al forzar un
4° use case en un controller ya en el umbral de 3.

Router nuevo `perfil_router.py`, prefix `/usuarios/me`, protegido con `get_current_user` (JWT
válido, sin restricción de rol — ya existe en `dependencies.py`, sin necesidad de un
`require_rol` nuevo).

## Componentes a Implementar

### 1. Entities (`src/identidad/entities/`)

- [x] `errors.py`
  - `PasswordActualIncorrecta` — nuevo error, mismo shape que `CredencialesInvalidas`
    (atributo `evento_cuenta_bloqueada: CuentaBloqueada | None`, se completa si este fallo es
    el 3er consecutivo)
- [x] `eventos.py`
  - `PasswordCambiada` — nuevo evento (`usuario_id`, `ocurrido_en`); `CuentaBloqueada` se
    reutiliza tal cual (su docstring ya anticipa el flujo de cambio de contraseña, `US-2.2.1`)
- [x] `usuario.py`
  - `cambiar_password(self, password_hash_nuevo: str) -> None` — fija el hash nuevo y resetea
    `intentos_fallidos_password` a 0 (mutación de estado pura, mismo estilo que
    `resetear_password` de `US-2.2.4`)
  - `registrar_fallo_cambio_password(self) -> bool` — incrementa
    `intentos_fallidos_password`; si llega a 3, fija `bloqueada = True`; devuelve si la cuenta
    quedó bloqueada por este fallo (el use case decide si arma `CuentaBloqueada`) — mismo
    patrón que el contador de login en `IniciarSesionUseCase`, pero encapsulado en la entidad
    en vez del use case, consistente con `resetear_password`/`cambiar_password` ya siendo
    métodos de `Usuario`

### 2. Use Case (`src/identidad/use_cases/`)

- [x] `cambiar_password.py`
  - `CambiarPasswordUseCase(usuario_repositorio: UsuarioRepositoryPort, hasher: PasswordHasherPort)`
  - `execute(usuario_id, password_actual, password_nueva) -> PasswordCambiada`
  - Orden: `obtener_por_id` → si `bloqueada`, `CuentaBloqueadaError` sin verificar nada → si
    `password_actual` no verifica, `usuario.registrar_fallo_cambio_password()` +
    `actualizar()` + `PasswordActualIncorrecta` (con `evento_cuenta_bloqueada` si corresponde)
    → `Usuario.validar_password_nueva(password_nueva)` (`PasswordDemasiadoCorta` si falla, sin
    tocar estado) → hash → `usuario.cambiar_password(hash)` → `actualizar()` → devuelve
    `PasswordCambiada`
  - Reutiliza `UsuarioRepositoryPort.obtener_por_id()`/`.actualizar()` (ya existen desde
    `US-2.2.1`/`.3`/`.4`) y `PasswordHasherPort` — sin puertos nuevos

### 3. Interface Adapters (`src/identidad/interface_adapters/`)

- [x] `controllers/perfil_controller.py`
  - `PerfilController(cambiar_password: CambiarPasswordUseCase)`
  - `async def cambiar_password(self, usuario_id, password_actual, password_nueva) -> PasswordCambiada`
    — delega directo, sin lógica adicional

### 4. Frameworks (`src/identidad/frameworks/`)

- [x] `api/schemas.py`
  - `CambiarPasswordRequest` — `password_actual: str`, `password_nueva: str = Field(..., min_length=8)`
- [x] `api/perfil_router.py` (nuevo)
  - `PUT /usuarios/me/password`, `dependencies` ninguna especial en el decorator — el usuario
    autenticado se resuelve vía `Depends(get_current_user)` como parámetro (necesitamos su
    `usuario_id`, no solo validar el rol)
  - Mapeo de errores: `CuentaBloqueadaError` → 403 (mismo criterio que `auth_router.py`),
    `PasswordActualIncorrecta` → 401 (mismo criterio que `CredencialesInvalidas`),
    `PasswordDemasiadoCorta` → 422 (mismo criterio que `cuentas_router.py`)
  - Response: 204 No Content en éxito (no hay body útil que devolver — a diferencia de
    `resetear_password`, acá no hay `comision_id`/detalle que un Administrador necesite ver)
- [x] `dependencies.py`
  - `get_perfil_controller(session: SessionDep) -> PerfilController` — arma
    `CambiarPasswordUseCase(SQLAlchemyUsuarioRepository(session), get_password_hasher())`

### 5. Integración

- [x] `src/app.py` — registrar `perfil_router` (mismo patrón que los otros routers de
  `identidad`)

**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-08-20

## Métricas de Tiempo

| Fase | Elapsed |
|------|---------|
| Fase 0 — Validación de Contexto | 62s |
| Fase 1 — Escenarios BDD | 174s |
| Fase 2 — Plan de Implementación | 986s |
| Fase 3 — Implementación (9 tareas) | 344s |
| Fase 4 — Tests Unitarios | 131s |
| Fase 5 — Tests de Integración | 189s |
| Fase 6 — Validación BDD | 268s |
| Fase 7 — Quality Gates | 903s |
| **Total (Fases 0–7)** | **~53 min** |

## Lecciones Aprendidas

- ✅ Separar el controller por actor (self-service vs. administración) desde el diseño en
  Fase 2 — no solo por command/query como en `US-2.2.2` — evitó de nuevo el patrón recurrente
  de CRITICAL de CBO en pre-push que afectó a `US-2.1.2`/`.5`/`.6`/`US-2.2.2`.
- ⚠️ `usuario_repositorio.guardar()` no persiste `bloqueada`/los contadores de intentos —
  solo `password_hash`, `nombre`, `email`, `creado_en` y el perfil. Un test que arma
  `Usuario.crear()` + `usuario.bloqueada = True` + `guardar()` para simular una cuenta ya
  bloqueada queda con una aserción trivialmente verdadera si no se llama también a
  `actualizar()` después — se detectó al escribir el test de integración de "cuenta ya
  bloqueada" de esta US (falló con 204 en vez de 403 hasta corregirlo). El mismo patrón débil
  está en el test equivalente de `US-2.2.4` (`test_reseteo_de_cuenta_bloqueada_la_desbloquea`)
  sin que fallara ahí porque su aserción no depende de que el bloqueo se haya persistido.
- 💡 Encapsular el contador de fallos en un método de la entidad
  (`registrar_fallo_cambio_password()`) en vez de mutar el campo directo en el use case
  (como hace `IniciarSesionUseCase` con `intentos_fallidos_login`) deja el use case más corto
  y hace el comportamiento de bloqueo testeable de forma aislada, sin pasar por el use case
  completo — dos estilos conviven en el BC (login: lógica en el use case; cambio de password:
  lógica en la entidad), ambos válidos, elegir según si el efecto es reutilizable fuera del
  flujo puntual.
