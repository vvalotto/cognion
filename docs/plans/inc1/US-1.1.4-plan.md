# Plan de Implementación: US-1.1.4 - Docente, administrador y estudiante se autentican y reciben un JWT con su rol

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** backend (BC Identidad)
**Alcance:** solo backend — frontend diferido (ver `docs/plans/inc1/US-1.1.4-context.md`)
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-07-23

## Métricas de Tiempo (tracker_cli)

| Fase | Tiempo real |
|------|-------------|
| 0 — Contexto | 44s |
| 1 — Escenarios BDD | 23s |
| 2 — Plan de Implementación | 152s |
| 3 — Implementación (14 tareas) | 289s |
| 4 — Tests Unitarios | 142s |
| 5 — Tests de Integración | 138s |
| 6 — Validación BDD | 151s |
| 7 — Quality Gates | 428s |
| **Total (hasta Fase 7)** | **~28 min** |

> Estimaciones humanas de PRIN-001 no aplican — el tracking mide tiempo real de ejecución del
> agente, no comparable con esfuerzo humano estimado en los templates de fase.

## Lecciones Aprendidas

- 💡 `Usuario.tipo_perfil` (`TipoPerfil`) ya cumplía el rol que la spec pedía como VO `Rol`
  nuevo — detectarlo en la Fase 2 evitó una abstracción redundante.
- 💡 `ACCESS_TOKEN_EXPIRE_MINUTES` llevaba desde el walking skeleton en 30 min, desalineado
  con `ADR-013` (60 min) — implementar el invariante de expiración fue la oportunidad natural
  de corregirlo en `settings.py`, `.env` y `.env.example`.
- ✅ Reutilizar el patrón exacto de `RegistrarEstudianteUseCase`/`RegistroController` (mismo
  BC, misma US-IEDD anterior) redujo a cero las decisiones de diseño en Fase 3 — todas las
  tareas se completaron en segundos.

## Desviación respecto de la spec — VO `Rol`

La spec (`docs/specs/inc1/US-1.1.4.md`) lista `src/identidad/entities/rol.py` como un VO
nuevo derivado del tipo de `perfil`. Esa derivación **ya existe**: `Usuario.tipo_perfil`
(`src/identidad/entities/usuario.py`) devuelve `TipoPerfil`, un `StrEnum` con los mismos tres
valores (`administrador`, `docente`, `estudiante`) que se usaría como claim `rol`. Crear un VO
`Rol` adicional sería una envoltura sin comportamiento propio sobre `TipoPerfil` — se usa
`TipoPerfil` directamente como claim, sin archivo `rol.py` nuevo. Aprobado por el usuario antes
de implementar.

## Componentes a Implementar

### 1. Entities (BC Identidad)
- [x] `src/identidad/entities/errors.py`
  - Agregar `CredencialesInvalidas`: excepción sin datos del email en el mensaje (no debe
    filtrar si la cuenta existe)
- [x] `src/identidad/entities/eventos.py`
  - Agregar `SesionIniciada(usuario_id, rol, ocurrido_en)`
- [x] `src/identidad/entities/jwt.py` (nuevo)
  - VO `JWT` — `frozen dataclass(token: str, rol: TipoPerfil, expira_en: datetime)`
- [x] `src/identidad/entities/ports/jwt_issuer_port.py` (nuevo)
  - `JWTIssuerPort.emitir(usuario_id: UUID, rol: TipoPerfil) -> JWT`
- [x] `src/identidad/entities/ports/usuario_repository_port.py`
  - Agregar `obtener_por_email(email: str) -> Usuario | None`

### 2. Use Cases
- [x] `src/identidad/use_cases/iniciar_sesion.py` (nuevo)
  - `IniciarSesionUseCase(usuario_repositorio, hasher, jwt_issuer)`
  - `execute(email, password) -> tuple[JWT, SesionIniciada]`
  - Busca por email; si no existe o el password no verifica: `CredencialesInvalidas`
    (mismo mensaje en ambos casos — INV de la spec)
  - Si verifica: emite JWT vía `jwt_issuer.emitir(usuario.id, usuario.tipo_perfil)` y arma
    `SesionIniciada`

### 3. Interface Adapters
- [x] `src/identidad/interface_adapters/gateways/usuario_repository.py`
  - Implementar `obtener_por_email`: query por email + reutiliza `_resolver_perfil` existente
- [x] `src/identidad/interface_adapters/controllers/auth_controller.py` (nuevo)
  - `AuthController(iniciar_sesion: IniciarSesionUseCase)`
  - `iniciar_sesion(email, password) -> tuple[JWT, SesionIniciada]`

### 4. Frameworks
- [x] `src/settings.py`
  - Corregir `access_token_expire_minutes` default de 30 → 60 (ADR-013 fija 60 min; el
    default actual quedó desalineado desde el walking skeleton)
- [x] `.env` / `.env.example`
  - Alinear `ACCESS_TOKEN_EXPIRE_MINUTES=60`
- [x] `src/identidad/frameworks/security/jwt_pyjwt.py` (nuevo)
  - `PyJWTIssuer(JWTIssuerPort)` — firma con `settings.secret_key`/`algorithm`, `exp` a
    `settings.access_token_expire_minutes` desde la emisión, claim `rol`
- [x] `src/identidad/frameworks/api/schemas.py`
  - Agregar `LoginRequest(email, password)`, `LoginResponse(access_token, token_type, rol, expira_en)`
- [x] `src/identidad/frameworks/api/auth_router.py` (nuevo)
  - `POST /identidad/login` — 200 con `LoginResponse`; 401 genérico con `CredencialesInvalidas`
- [x] `src/identidad/frameworks/dependencies.py`
  - `get_jwt_issuer() -> JWTIssuerPort`, `get_auth_controller(session) -> AuthController`
- [x] `src/app.py`
  - `app.include_router(auth_router)`

### 5. Integración
- [x] Registrar `auth_router` en `src/app.py`
- [x] Verificar `PyJWT[crypto]` ya declarado en `pyproject.toml` (ADR-007) — no requiere
      cambio de dependencias

**Estado:** 14/14 tareas completadas — smoke test manual con `TestClient` confirmó
`POST /identidad/login` responde 401 genérico ante credenciales inválidas.
