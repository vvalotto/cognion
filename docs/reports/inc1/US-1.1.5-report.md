# Reporte de Implementación: US-1.1.5

## Resumen Ejecutivo

- **Historia de Usuario:** US-1.1.5 - El sistema restringe el acceso a funcionalidades
  según el rol del usuario autenticado
- **Puntos estimados:** 5
- **Tiempo real:** ~29 min (fases 0-8, tracking de ejecución del agente, no comparable
  contra esfuerzo humano — nota PRIN-001 del skill `implement-us`)
- **Estado:** ✅ COMPLETADO (backend) — sin pantalla propia (no aplica frontend, ver
  `## Fuente de verdad UX` de la spec)
- **Fecha completado:** 2026-07-24

Última US de la Iteración 1 (BC Identidad): agrega el guard de autorización (RBAC) que hace
cumplir RF-02 sobre el JWT emitido en `US-1.1.4` — hasta esta US, cualquier `Usuario`
autenticado podía invocar cualquier endpoint. Implementa dos dependencies FastAPI
(`get_current_user`, `require_rol`) que decodifican y validan el JWT, y verifican el claim
`rol` contra una lista de roles permitidos declarada por endpoint. Con esto, RF-02 pasa a
Implementado y la Iteración 1 completa queda cerrada en backend.

---

## Componentes Implementados

### Entities (`src/identidad/entities/`)
- ✅ `jwt.py` (editado) — VO `JWTPayload(usuario_id, rol)`, resultado de decodificar un JWT
  válido sin volver a consultar la base (ADR-013)
- ✅ `errors.py` (editado) — `JWTInvalido`, `JWTExpirado`
- ✅ `ports/jwt_issuer_port.py` (editado) — método abstracto `verificar(token) -> JWTPayload`

### Frameworks/security (`src/identidad/frameworks/security/`)
- ✅ `jwt_pyjwt.py` (editado) — `PyJWTIssuer.verificar()`: `jwt.decode(...)`,
  `ExpiredSignatureError` → `JWTExpirado`, `InvalidTokenError` → `JWTInvalido`

### Interface Adapters (`src/identidad/interface_adapters/security/`, nuevo paquete)
- ✅ `get_current_user.py` (nuevo) — `build_get_current_user(jwt_issuer)`: builder que recibe
  la abstracción `JWTIssuerPort` (no `frameworks/`) y arma la dependency que extrae el JWT del
  header `Authorization: Bearer` vía `fastapi.security.HTTPBearer`; 401 si falta o no es válido
- ✅ `require_rol.py` (nuevo) — `require_rol(roles_permitidos, get_current_user)`: builder que
  compone sobre `get_current_user` y exige el rol; 403 si no está permitido

### Frameworks (`src/identidad/frameworks/`)
- ✅ `dependencies.py` (editado) — composition root: `get_current_user`,
  `require_administrador`, `require_docente` (wiring de `PyJWTIssuer` con los builders)
- ✅ `api/usuarios_router.py` (editado) — `crear_usuario` con `require_administrador`
- ✅ `api/comisiones_router.py` (editado) — `crear_comision`, `asignar_docente` con
  `require_administrador`
- ✅ `api/invitaciones_router.py` (editado) — `generar_invitacion` con `require_docente`

`auth_router.py` (login) y `registro_router.py` (registro por invitación) permanecen
públicos — son la precondición de tener un JWT.

### Desviación de alcance respecto de la spec
- Ninguna. Implementación 1:1 con `docs/specs/inc1/US-1.1.5.md` y el plan de Fase 2.

---

## API Endpoints Afectados

| Método | Ruta | Descripción | Auth |
|--------|------|--------------|------|
| POST | `/usuarios` | Alta de usuario (`US-1.1.0`) | `require_administrador` |
| POST | `/comisiones` | Alta de comisión (`US-1.1.0`) | `require_administrador` |
| POST | `/comisiones/{id}/docentes` | Asignar docente (`US-1.1.0`) | `require_administrador` |
| POST | `/comisiones/{id}/invitaciones` | Generar invitación (`US-1.1.1`) | `require_docente` |
| POST | `/identidad/login` | Login (`US-1.1.4`) | Público |
| POST | `/identidad/registro` | Registro por invitación (`US-1.1.2`) | Público |

**Respuestas nuevas:** `401` (`JWTInvalido`/`JWTExpirado`/sin header), `403` (rol insuficiente)

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint | 9.96/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 4 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (mínimo) | 61.62 (grado A) | > 20 | ✅ |
| Cobertura de Tests | 100% (entities/interface_adapters nuevos) | ≥ 95.0% | ✅ |
| mypy (`src/` completo) | 0 errores | — | ✅ |

Fuente: `quality/reports/inc1/US-1.1.5-quality.json`. `frameworks/` queda fuera del cálculo
de coverage por convención del proyecto (`pyproject.toml [tool.coverage.run] omit`), igual
que en US-1.1.4 — se cubre igual con tests unitarios reales en `test_jwt_pyjwt.py`.

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Tests Unitarios (12 tests nuevos) — `tests/unit/inc1/`
- `test_jwt_pyjwt.py` (editado, +5 tests) — `PyJWTIssuer.verificar()`: token válido, expirado,
  firma inválida, malformado, sin claim `rol`
- `test_get_current_user.py` (nuevo, 4 tests) — token válido, sin header, inválido, expirado
- `test_require_rol.py` (nuevo, 4 tests) — rol permitido, rol entre varios permitidos, rol no
  permitido, docente rechazado en administración
- `_fakes.py` (editado) — `FakeJWTIssuer.verificar()` (implementa el método abstracto nuevo)

### Tests de Integración (6 tests nuevos + 3 archivos actualizados) — `tests/integration/inc1/`
- `test_autorizacion_rbac_integration.py` (nuevo, 6 tests) — acceso concedido, estudiante
  rechazado en administración/invitaciones, docente rechazado en administración, sin JWT,
  JWT expirado
- `test_usuarios_api_integration.py`, `test_comisiones_api_integration.py`,
  `test_invitaciones_api_integration.py` (editados) — agregan headers de autorización, ahora
  requeridos por los endpoints protegidos
- `conftest.py` (editado) — fixtures `admin_headers`/`docente_headers`

### Escenarios BDD (6 escenarios) — `tests/features/inc1/US-1.1.5-autorizacion-rbac.feature`
- Acceso concedido con rol suficiente
- Estudiante rechazado en gestión del banco de preguntas / analytics globales (validados
  contra endpoints reales de Identidad — banco de preguntas/analytics no existen en este
  incremento, ver nota de implementación de la spec)
- Docente rechazado en administración de cuentas
- Request sin JWT
- JWT expirado

`tests/step_defs/inc1/_auth_headers.py` (nuevo) — helper compartido que emite JWTs directo
con `PyJWTIssuer` (no vía API), reutilizado también por `test_us_1_1_0_steps.py` a
`test_us_1_1_4_steps.py`, actualizados en esta US porque sus fixtures de setup dejaron de
funcionar al proteger `/usuarios`, `/comisiones` e `/comisiones/{id}/invitaciones`.

**Todos los tests pasando:** ✅ 132/132 (suite completa del proyecto)

---

## Archivos Creados/Modificados

**Producción:** `src/identidad/entities/jwt.py`, `entities/errors.py`,
`entities/ports/jwt_issuer_port.py`, `frameworks/security/jwt_pyjwt.py`,
`frameworks/dependencies.py`, `frameworks/api/{usuarios,comisiones,invitaciones}_router.py`
(editados); `interface_adapters/security/{get_current_user,require_rol}.py` (nuevos,
paquete nuevo) — ~110 líneas netas.

**Tests:** `tests/unit/inc1/test_jwt_pyjwt.py`, `tests/unit/inc1/_fakes.py` (editados);
`tests/unit/inc1/test_{get_current_user,require_rol}.py` (nuevos);
`tests/integration/inc1/test_autorizacion_rbac_integration.py` (nuevo);
`tests/integration/inc1/test_{usuarios,comisiones,invitaciones}_api_integration.py`,
`tests/integration/conftest.py` (editados);
`tests/features/inc1/US-1.1.5-autorizacion-rbac.feature`,
`tests/step_defs/inc1/test_us_1_1_5_steps.py`, `tests/step_defs/inc1/_auth_headers.py`
(nuevos); `tests/step_defs/inc1/test_us_1_1_{0,1,2,3,4}_steps.py` (editados) — ~650 líneas.

**Documentación:** `docs/plans/inc1/US-1.1.5-{context,plan}.md`,
`docs/reports/inc1/US-1.1.5-report.md` (este archivo),
`quality/reports/inc1/US-1.1.5-{quality,codeguard}.json`, `docs/traceability/matrix.md`
(editado), `CHANGELOG.md` (editado).

---

## Criterios de Aceptación

- [x] Acceso concedido con rol suficiente → handler ejecutado (201)
- [x] Estudiante rechazado en gestión del banco de preguntas → 403
- [x] Estudiante rechazado en analytics globales → 403
- [x] Docente rechazado en administración de cuentas → 403
- [x] Request sin header `Authorization` → 401
- [x] JWT expirado → 401

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] US-IEDD de infraestructura frontend (router + cliente API), diferida desde `US-1.1.2`
  y acumulada por cada US de Identidad desde entonces — incluiría el manejo de 401/403 en el
  cliente
- [ ] Con RF-01 y RF-02 implementados, la Iteración 1 del Incremento 1 queda completa —
  siguiente paso es evaluar el cierre del Incremento 1 (Baseline BL-002) según
  `docs/plans/PLAN-CM.md` §7
- [ ] Al definir Banco de Preguntas y Analytics (Incremento 2+), extender la matriz rol→recurso
  con `require_rol` sobre sus propios routers, reutilizando el mismo mecanismo

---

## Lecciones Aprendidas

- ⚠️ Proteger endpoints ya existentes con un guard transversal (RBAC) rompe cualquier test que
  los invocara sin autenticación — hubo que revisar y actualizar toda la suite de integración
  y BDD de las US anteriores del mismo BC, no solo agregar tests nuevos. Alcance mayor al
  anticipado en el plan de Fase 2.
- 💡 El problema huevo-y-gallina del primer Administrador (no puede autenticarse contra la API
  para crear su propia cuenta) se resuelve en tests emitiendo el JWT directo con
  `PyJWTIssuer`, sin pasar por `/identidad/login` — el mismo patrón que tendría un
  seed/fixture en un despliegue real.
- 💡 Los builders (`build_get_current_user`, `require_rol`) reciben la abstracción como
  parámetro en vez de importar la implementación concreta — mantiene `interface_adapters/`
  sin depender de `frameworks/`, con el wiring centralizado en el composition root
  (`frameworks/dependencies.py`), igual que ya se hacía con los controllers existentes.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-07-24
