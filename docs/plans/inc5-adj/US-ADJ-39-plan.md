# Plan de Implementación: US-ADJ-39 - Confirmar nueva contraseña con token de recuperación

**Patrón:** clean-architecture (BC-first: entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion
**BC:** identidad

## Componentes a Implementar

### 1. Entities

- [x] `src/identidad/entities/errors.py`
  - `TokenRecuperacionInvalido(token: str)` — mismo patrón que `InvitacionInvalida`
  - `TokenRecuperacionYaUsado(token: str)` — mismo patrón que `InvitacionYaUsada`
  - `TokenRecuperacionVencido(token: str)` — mismo patrón que `InvitacionVencida`

- [x] `src/identidad/entities/token_recuperacion_password.py`
  - Método `verificar_vigente(ahora: datetime) -> None`: lanza `TokenRecuperacionYaUsado` si
    `usado_en is not None`, o `TokenRecuperacionVencido` si `ahora >= expira_en` (INV-ID-13).
    Mismo patrón que `Invitacion.verificar_vigente()`. No lanza nada si el token es vigente.
  - El marcado de "usado" tras el canje reutiliza `invalidar(ahora)`, ya existente y ya
    pensado para este caso (ver su docstring) — sin método nuevo.

- [x] `src/identidad/entities/usuario.py`
  - Método `recuperar_password(password_hash_nuevo: str) -> None`: fija `password_hash_nuevo`
    sin tocar `bloqueada` ni `intentos_fallidos_login`/`intentos_fallidos_password` — distinto
    de `resetear_password()` (desbloquea) y `cambiar_password()` (resetea el contador de
    intentos de cambio). Necesario porque ningún método existente cumple la postcondición
    explícita de la spec: "una cuenta bloqueada sigue bloqueada tras este flujo", sin tocar
    tampoco los contadores.

- [x] `src/identidad/entities/eventos.py`
  - `PasswordRecuperada(usuario_id: UUID, ocurrido_en: datetime)` — mismo shape que
    `PasswordCambiada`, sin `administrador_id` (autoservicio, no acción de un Administrador).

### 2. Use Cases

- [x] `src/identidad/use_cases/confirmar_nueva_password.py`
  - `ConfirmarNuevaPasswordUseCase.execute(token: str, password_nueva: str) -> tuple[Usuario, PasswordRecuperada]`
  - Flujo: busca el token por valor (`TokenRecuperacionInvalido` si no existe) →
    `token.verificar_vigente(ahora)` → busca el `Usuario` dueño del token →
    `Usuario.validar_password_nueva(password_nueva)` (INV-ID-11 ampliada) → hashea →
    `usuario.recuperar_password(password_hash)` → persiste `usuario` → `token.invalidar(ahora)`
    → persiste `token` → arma y devuelve `PasswordRecuperada`.
  - Mismo patrón de persistencia secuencial (usuario primero, luego token) que
    `RegistrarEstudianteUseCase` (`US-1.1.6`) usa para `Usuario`/`Invitacion` — no introduce
    unit-of-work nuevo, fuera del alcance de esta US.

### 3. Interface Adapters

- [x] `src/identidad/interface_adapters/controllers/recuperacion_password_controller.py`
  - Agrega el segundo caso de uso ya inyectado (`ConfirmarNuevaPasswordUseCase`) y un método
    `confirmar(token: str, password_nueva: str) -> Usuario` que delega y descarta el evento
    (mismo criterio que `solicitar()` con `SolicitarRecuperacionPasswordUseCase`).

### 4. Frameworks

- [x] `src/identidad/frameworks/api/schemas.py`
  - `ConfirmarRecuperacionPasswordRequest(token: str, password_nueva: str)`
  - `ConfirmarRecuperacionPasswordResponse(mensaje: str)` — mensaje de éxito fijo

- [x] `src/identidad/frameworks/api/recuperacion_password_router.py`
  - `POST /identidad/recuperar-password/confirmar`, público, sin JWT, `200 OK`.
  - Mapeo de excepciones (mismo patrón que `registro_router.py`, todas a 422 —
    `TokenRecuperacionInvalido`/`TokenRecuperacionYaUsado`/`TokenRecuperacionVencido`/
    `PasswordDemasiadoCorta`/`PasswordSinComplejidadSuficiente`).

- [x] `src/identidad/frameworks/dependencies.py`
  - `get_recuperacion_password_controller()`: agrega `ConfirmarNuevaPasswordUseCase` al mismo
    controller ya cableado para `solicitar()`.

## Integración

- [x] Ningún puerto nuevo — reutiliza `TokenRecuperacionPasswordRepositoryPort.actualizar()` y
  `UsuarioRepositoryPort.actualizar()`, ambos ya implementados.
- [x] Ningún gateway nuevo — `SQLAlchemyTokenRecuperacionPasswordRepository` y
  `SQLAlchemyUsuarioRepository` ya soportan la operación requerida.

**Estado:** 9/9 tareas completadas

## Progreso de fases posteriores

**Fase 4 (tests unitarios):** 12 tests nuevos en `tests/unit/inc1/` (mismo criterio que
`US-ADJ-38` — la BC Identidad usa `tests/unit/inc1/` como home de sus unit tests
independientemente del incremento que los agregue): `test_token_recuperacion_password.py`
(5 tests de `verificar_vigente`), `test_usuario.py` (3 tests de `recuperar_password`),
`test_confirmar_nueva_password_use_case.py` (7 tests, nuevo), `test_recuperacion_password_controller.py`
(actualizado a la firma de 2 use cases). 100% cobertura en los 6 componentes tocados, 483/483
tests unitarios en verde.

**Fase 5 (tests de integración):** 6 tests nuevos en
`tests/integration/inc1/test_confirmar_recuperacion_password_api_integration.py` (happy path
con login real post-canje, token ya usado, vencido, inexistente, password débil, cuenta
bloqueada que sigue bloqueada). 86/86 tests de integración de `inc1` en verde.

**Fase 6 (BDD):** `tests/step_defs/inc5-adj/test_us_adj_39_steps.py`, mismo patrón que
`US-ADJ-38` (steps sync con `run_async`, `ADR-018`). 6/6 escenarios en verde. Suite completa
de `tests/step_defs/` 230/231 (el único fallo es el flake preexistente de
`test_us_3_2_1_steps.py` ya documentado en `CLAUDE.md`, ajeno a esta US).

**Fase 7 (quality gates):** pylint 9.96/10, CC máx 8 (pre-existente en
`Usuario.validar_password_nueva`), MI mín 57.53, coverage 100% en los 6 componentes de
negocio tocados (`frameworks/` queda fuera del gate por `pyproject.toml`). Único fix real:
línea larga en `errors.py:159` (`TokenRecuperacionInvalido` docstring). Mismo gap de entorno
que `US-ADJ-38` en `codeguard` (vulture/codespell no instalados, pylint por archivo aislado
da falsos negativos en `router.py`/`schemas.py` corregidos al correr junto al resto).

**Nota operativa:** correr `tests/integration/` y `tests/step_defs/` truncó la base de datos
local compartida (comportamiento conocido, ver memoria del proyecto) — no había ninguna
sesión manual en curso (`BL-008` ya había cerrado la prueba de estabilización el
2026-09-10). Se reseeded el Administrador (`admin@fiuner.edu.ar`) después de cada corrida;
los datos de la prueba manual de estabilización (17 estudiantes, docentes, materias,
comisiones) no se restauraron — quedan disponibles para recargar con los scripts de
`tests/uat/datos-reales/` si hace falta.
