# Plan de Implementación: US-1.1.5 - El sistema restringe el acceso según el rol del usuario autenticado

**Patrón:** Clean Architecture (entities → use_cases → interface_adapters → frameworks, BC-first)
**Producto:** backend (BC Identidad)
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-07-24

## Componentes a Implementar

### 1. Entities — extensión de `JWTIssuerPort` y errores de dominio
- [x] `src/identidad/entities/jwt.py`
  - Agregar `JWTPayload` (dataclass frozen): `usuario_id: UUID`, `rol: TipoPerfil` — resultado de
    decodificar un JWT válido, sin volver a golpear la base (ADR-013, sin refresh/blacklist)
- [x] `src/identidad/entities/errors.py`
  - Agregar `JWTInvalido` — token ausente/malformado/con firma inválida
  - Agregar `JWTExpirado` — token cuyo `exp` ya pasó
- [x] `src/identidad/entities/ports/jwt_issuer_port.py`
  - Agregar método abstracto `verificar(self, token: str) -> JWTPayload` — decodifica y valida
    el token recibido, levanta `JWTInvalido`/`JWTExpirado`

### 2. Frameworks/security — implementación concreta de verificación
- [x] `src/identidad/frameworks/security/jwt_pyjwt.py`
  - Implementar `PyJWTIssuer.verificar()` con `jwt.decode(...)`
  - `jwt.ExpiredSignatureError` → `JWTExpirado`; `jwt.InvalidTokenError` → `JWTInvalido`

### 3. Interface Adapters/security — dependencies FastAPI reutilizables
- [x] `src/identidad/interface_adapters/security/get_current_user.py`
  - `build_get_current_user(jwt_issuer: JWTIssuerPort) -> Callable` — builder que closura sobre
    el puerto (abstracción, no la implementación concreta) y arma la dependency real
  - Extrae el `Authorization: Bearer <token>` vía `fastapi.security.HTTPBearer(auto_error=False)`
  - Sin header → `HTTPException(401)`; `JWTInvalido`/`JWTExpirado` → `HTTPException(401)`
  - Devuelve `JWTPayload` (usuario_id + rol) si el token es válido
- [x] `src/identidad/interface_adapters/security/require_rol.py`
  - `require_rol(roles_permitidos: list[TipoPerfil], get_current_user: Callable) -> Callable` —
    builder que compone sobre `get_current_user` y valida `usuario.rol in roles_permitidos`
  - Rol insuficiente → `HTTPException(403)`

> **Nota de capas:** ambos builders reciben la dependencia concreta (`JWTIssuerPort`,
> `get_current_user`) como parámetro — no importan `frameworks/` directamente. El wiring con la
> implementación concreta (`PyJWTIssuer`) ocurre en el composition root (`frameworks/dependencies.py`),
> igual que ya se hace con los controllers existentes.

### 4. Integración — composition root y routers protegidos
- [x] `src/identidad/frameworks/dependencies.py`
  - `get_current_user = build_get_current_user(get_jwt_issuer())`
  - `require_administrador = require_rol([TipoPerfil.ADMINISTRADOR], get_current_user)`
  - `require_docente = require_rol([TipoPerfil.DOCENTE], get_current_user)`
- [x] `src/identidad/frameworks/api/usuarios_router.py`
  - `crear_usuario` → agregar `dependencies=[Depends(require_administrador)]`
- [x] `src/identidad/frameworks/api/comisiones_router.py`
  - `crear_comision` y `asignar_docente` → agregar `dependencies=[Depends(require_administrador)]`
- [x] `src/identidad/frameworks/api/invitaciones_router.py`
  - `generar_invitacion` → agregar `dependencies=[Depends(require_docente)]`

> `auth_router.py` (login) y `registro_router.py` (registro por invitación) quedan sin proteger —
> son los únicos endpoints públicos del BC (precondición de tener un JWT), consistente con la spec.

**Estado:** 10/10 tareas completadas

## Métricas de Tiempo

| Fase | Tiempo real |
|------|-------------|
| Validación de Contexto | 84s |
| Escenarios BDD | 71s |
| Plan de Implementación | 120s |
| Implementación | 412s |
| Tests Unitarios | 194s |
| Tests de Integración | 224s |
| Validación BDD | 312s |
| Quality Gates | 341s |
| **Total** | **~29 min** |

> Nota (PRIN-001, `.claude/skills/implement-us/skill.md`): estos tiempos son ejecución real del
> agente, no comparables contra estimaciones de esfuerzo humano.

## Lecciones Aprendidas

- ⚠️ Proteger endpoints existentes con RBAC rompió los `step_defs`/tests de integración de
  `US-1.1.0` a `US-1.1.4` (llamadas sin JWT a `/usuarios`, `/comisiones`, `/comisiones/{id}/invitaciones`)
  — hubo que actualizar 5 archivos de step_defs + 3 archivos de tests de integración +
  `tests/integration/conftest.py`. Alcance no anticipado en el plan de Fase 2, cubierto en
  Fase 5/6 sin volver a Fase 2.
- 💡 Emitir el JWT del primer Administrador directo con `PyJWTIssuer` (sin pasar por la API)
  resuelve el problema huevo-y-gallina en tests — mismo patrón que tendría un seed/fixture de
  despliegue real (ver nota de `US-1.1.0` en `docs/plans/inc1/inc1-candidatas.md`).
- 💡 Los builders (`build_get_current_user`, `require_rol`) reciben la abstracción como
  parámetro en vez de importar la implementación concreta — mantiene `interface_adapters/`
  sin depender de `frameworks/`, con el wiring centralizado en el composition root
  (`frameworks/dependencies.py`), igual que ya se hacía con los controllers.
