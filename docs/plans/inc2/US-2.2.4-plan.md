# Plan de Implementación: US-2.2.4 - Administrador resetea la contraseña de una cuenta

**Patrón:** Clean Architecture BC-First (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion — BC Identidad

## Decisión de diseño (a confirmar)

INV-ID-11 (mínimo 8 caracteres) nunca se validó del lado de dominio hasta ahora — `CrearUsuario`
y `RegistrarEstudiante` solo la enforzan vía `Field(min_length=8)` en el schema Pydantic, no en
`Usuario`. Como esta US es la primera en requerir `PasswordDemasiadoCorta` como error de dominio
(probado a nivel de entidad/caso de uso, no solo HTTP), agrego a `Usuario`:

- `Usuario.validar_password_nueva(password_nueva: str) -> None` — staticmethod, invariante
  reutilizable (queda lista para `US-2.2.5 CambiarPassword`, que declara la misma INV-ID-11).
- `usuario.resetear_password(password_hash_nuevo: str) -> bool` — método de instancia, mutación
  pura de estado (ya validado); devuelve `True` si la cuenta **estaba** bloqueada (para que el
  caso de uso decida si emite `CuentaDesbloqueada`).

El caso de uso valida la contraseña en texto plano *antes* de hashear (bcrypt no sirve para medir
longitud del plano), consistente con que `Usuario` es capa pura sin acceso al hasher.

## Componentes a Implementar

### 1. Entities
- [x] `src/identidad/entities/errors.py`
  - `PasswordDemasiadoCorta` — mensaje fijo, sin datos de instancia (no hay nada sensible que loguear)
- [x] `src/identidad/entities/eventos.py`
  - `PasswordReseteada(usuario_id, administrador_id, ocurrido_en)`
  - `CuentaDesbloqueada(usuario_id, ocurrido_en)` — mismo shape que `CuentaBloqueada` existente
- [x] `src/identidad/entities/usuario.py`
  - `Usuario.validar_password_nueva(password_nueva: str) -> None` (staticmethod)
  - `usuario.resetear_password(password_hash_nuevo: str) -> bool`

### 2. Use Cases
- [x] `src/identidad/use_cases/resetear_password.py`
  - `ResetearPasswordUseCase(usuario_repositorio, hasher)`
  - `execute(usuario_id, password_nueva, administrador_id) -> tuple[Usuario, PasswordReseteada, CuentaDesbloqueada | None]`
  - Orden: `obtener_por_id` (404 si no existe) → `validar_password_nueva` (422 si corta) →
    hash → `resetear_password` en la entidad → `actualizar` en el repositorio → armar eventos

### 3. Interface Adapters
- [x] `src/identidad/interface_adapters/controllers/cuentas_controller.py`
  - Inyectar `ResetearPasswordUseCase` como 3ra dependencia del controller existente
  - Método `resetear_password(usuario_id, password_nueva, administrador_id) -> Usuario`
    (devuelve solo la entidad actualizada — el router decide qué exponer; evita acoplar el
    controller al tipo de los eventos, mismo criterio que `US-2.1.5`/`US-2.1.6`)

### 4. Frameworks
- [x] `src/identidad/frameworks/api/schemas.py`
  - `ResetearPasswordRequest(password_nueva: str = Field(..., min_length=8))`
- [x] `src/identidad/frameworks/api/cuentas_router.py`
  - `POST /usuarios/{usuario_id}/resetear-password` (rol `administrador`, ya cubierto por
    `require_administrador` existente en este router)
  - Responde `200 OK` con `CuentaDetalleResponse` (reusa el schema de `US-2.2.3`)
  - Mapeo de errores: `UsuarioNoExiste` → 404 (patrón ya en este router),
    `PasswordDemasiadoCorta` → 422 (mismo patrón que `invitaciones_router`/`comisiones_router`)
- [x] `src/identidad/frameworks/dependencies.py`
  - `get_cuentas_controller` pasa a construir `ResetearPasswordUseCase(usuario_repo, get_password_hasher())`

### 5. Integración
- [x] Verificar que `administrador_id` llega desde el JWT (claim resuelto en `JWTPayload.usuario_id`
  vía `require_administrador` inyectado como parámetro, no del body) — evita que el cliente
  falsee quién ejecuta el reseteo

## Contingencia de CBO (pre-push)

`CuentasController` pasa de 2 a 3 use cases inyectados. Si `DesignReviewer` marca CRITICAL de
CBO en el pre-push (patrón ya visto 3 veces en `PreguntasController`, `US-2.1.2`/`.5`/`.6`), la
corrección es separar por responsabilidad command/query — un controller nuevo para comandos de
cuenta (`resetear_password`, y los que sigan en `US-2.2.5`/`.6`) dejando `CuentasController` solo
con las queries (`listar_cuentas`, `obtener_cuenta`). No se aplica preventivamente: se decide
recién si el gate lo pide.

**Estado:** ✅ COMPLETADO — 9/9 tareas de implementación (+ 5 tareas de tests: entidad, use case,
controller, integración API, step_defs BDD)
**Fecha completado:** 2026-08-20
**Tiempo total (tracker):** ~25 min efectivos

## Contingencia de CBO — resultado

No se disparó: `CuentasController` sigue con 3 métodos delgados (cada uno delega en un único
use case), sin ensanchar el acoplamiento de tipos del controller. Se revisará en el pre-push
gate del PR; si `DesignReviewer` marca CRITICAL, se aplica la separación command/query descripta
arriba.

## Resultado de Quality Gates (Fase 7)

pylint 9.95/10, CC máx 7 (preexistente, no en código de esta US), MI mín 48.58 (preexistente),
coverage 99% en `src/identidad` (100% en `resetear_password.py`), codeguard 0 errores/0
warnings. Detalle completo: `quality/reports/inc2/US-2.2.4-quality.json`.
