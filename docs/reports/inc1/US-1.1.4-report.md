# Reporte de Implementación: US-1.1.4

## Resumen Ejecutivo

- **Historia de Usuario:** US-1.1.4 - Docente, administrador y estudiante se autentican y
  reciben un JWT con su rol
- **Puntos estimados:** 5
- **Tiempo real:** ~28 min (fases 0-7, tracking de ejecución del agente, no comparable
  contra esfuerzo humano — nota PRIN-001 del skill `implement-us`)
- **Estado:** ✅ COMPLETADO (backend) — frontend diferido, mismo criterio que
  `US-1.1.1`/`US-1.1.2`/`US-1.1.3`
- **Fecha completado:** 2026-07-23

Quinta US de la Iteración 1 (BC Identidad) y punto de entrada común a los tres perfiles:
sin esta US, ninguna otra parte del sistema puede exigir un actor autenticado. Habilita
`US-1.1.5` (autorización por rol). Implementa `IniciarSesionUseCase`: verifica email y
contraseña (bcrypt) contra el `Usuario` persistido y emite un JWT (PyJWT, `ADR-007`) con
claim `rol` derivado de `Usuario.tipo_perfil`, expiración a 60 minutos sin refresh ni
blacklist (`ADR-013`). Rechazo con `CredencialesInvalidas` genérico tanto si el email no
existe como si la contraseña no verifica, para no filtrar existencia de cuentas.

---

## Componentes Implementados

### Entities (`src/identidad/entities/`)
- ✅ `jwt.py` (nuevo) — VO `JWT(token, rol, expira_en)`
- ✅ `ports/jwt_issuer_port.py` (nuevo) — `JWTIssuerPort.emitir(usuario_id, rol) -> JWT`
- ✅ `ports/usuario_repository_port.py` (editado) — `obtener_por_email(email) -> Usuario | None`
- ✅ `errors.py` (editado) — `CredencialesInvalidas`, mensaje genérico sin datos del intento
- ✅ `eventos.py` (editado) — `SesionIniciada(usuario_id, rol, ocurrido_en)`

### Use Cases (`src/identidad/use_cases/`)
- ✅ `iniciar_sesion.py` (nuevo) — `IniciarSesionUseCase.execute(email, password)`

### Interface Adapters
- ✅ `interface_adapters/gateways/usuario_repository.py` (editado) — `obtener_por_email`,
  refactor `_armar_usuario` compartido con `obtener_por_id`
- ✅ `interface_adapters/controllers/auth_controller.py` (nuevo) — delega al use case

### Frameworks (`src/identidad/frameworks/`)
- ✅ `security/jwt_pyjwt.py` (nuevo) — `PyJWTIssuer(JWTIssuerPort)`, PyJWT + `settings`
- ✅ `api/schemas.py` (editado) — `LoginRequest`, `LoginResponse`
- ✅ `api/auth_router.py` (nuevo) — `POST /identidad/login`
- ✅ `dependencies.py` (editado) — `get_jwt_issuer`, `get_auth_controller`
- ✅ `src/app.py` (editado) — registra `auth_router`
- ✅ `src/settings.py`, `.env`, `.env.example` (editados) — `ACCESS_TOKEN_EXPIRE_MINUTES`
  corregido de 30 a 60 min (alineado con `ADR-013`; quedó desalineado desde el walking
  skeleton)

### Desviación de alcance respecto de la spec
- **VO `Rol` no creado** — `Usuario.tipo_perfil` (`TipoPerfil`, `StrEnum` ya existente) cumple
  exactamente la misma función; un VO adicional sería una envoltura sin comportamiento propio.
  Decisión documentada y aprobada en Fase 2 (`docs/plans/inc1/US-1.1.4-plan.md`).

---

## API Endpoints

| Método | Ruta | Descripción | Auth |
|--------|------|--------------|------|
| POST | `/identidad/login` | Autentica y emite JWT con rol | Público — es el propio punto de entrada |

**Respuestas:** `200` (`access_token`, `token_type`, `rol`, `expira_en`), `401`
(`CredencialesInvalidas`, mismo mensaje ante email inexistente o password incorrecta)

**OpenAPI Docs:** `/docs`

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint | 10.0/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 3 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (mínimo) | 67.09 (grado A) | > 20 | ✅ |
| Cobertura de Tests | 100% (archivos nuevos) / 99% (proyecto) | ≥ 95.0% | ✅ |

Fuente: `quality/reports/inc1/US-1.1.4-quality.json`. Gate real del proyecto (ruff + mypy
strict + black + isort) también en verde — ver `CLAUDE.md` §Quality gates; pylint se corre
solo para completar este reporte.

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Tests Unitarios (10 tests nuevos) — `tests/unit/inc1/`
- `test_iniciar_sesion_use_case.py` (nuevo, 6 tests) — login exitoso por cada rol, rechazo
  por password incorrecta, rechazo por email inexistente, mensaje idéntico en ambos rechazos
- `test_auth_controller.py` (nuevo, 1 test) — delegación al use case
- `test_jwt_pyjwt.py` (nuevo, 3 tests) — claim `rol`, expiración de 60 min, un token por
  cada `TipoPerfil`
- `_fakes.py` (editado) — `FakeUsuarioRepository.obtener_por_email`, `FakeJWTIssuer`

### Tests de Integración (7 tests nuevos) — `tests/integration/inc1/`
- `test_auth_api_integration.py` (nuevo, 5 tests) — `POST /identidad/login` end-to-end
  contra PostgreSQL local, los tres roles + los dos rechazos
- `test_usuario_repository_integration.py` (editado, 2 tests) — `obtener_por_email`

### Escenarios BDD (5 escenarios) — `tests/features/inc1/US-1.1.4-autenticacion-jwt.feature`
- Login exitoso de un Docente (incluye claim `rol`, expiración 60 min, evento `SesionIniciada`)
- Login exitoso de un Administrador
- Login exitoso de un Estudiante
- Rechazo por contraseña incorrecta
- Rechazo por email inexistente (mismo mensaje que el caso anterior)

**Todos los tests pasando:** ✅ 107/107 (suite completa del proyecto)

---

## Ajuste de Alcance — Frontend Diferido (mismo criterio de US-1.1.1/2/3)

Se verificó `frontend/src`: sigue siendo el scaffold default de Vite, sin React Router ni
cliente HTTP. `Login.tsx`, `LoginError.tsx` y `frontend/src/lib/auth.ts` quedan diferidos a
la misma US-IEDD de frontend ya diferida desde `US-1.1.2`, una vez decidida la infraestructura
base (routing, cliente API, almacenamiento del JWT en el cliente).

---

## Archivos Creados/Modificados

**Producción:** `src/identidad/entities/jwt.py`, `entities/ports/jwt_issuer_port.py` (nuevos);
`entities/ports/usuario_repository_port.py`, `entities/errors.py`, `entities/eventos.py`,
`interface_adapters/gateways/usuario_repository.py`, `frameworks/dependencies.py`,
`frameworks/api/schemas.py`, `src/app.py`, `src/settings.py` (editados);
`use_cases/iniciar_sesion.py`, `interface_adapters/controllers/auth_controller.py`,
`frameworks/security/jwt_pyjwt.py`, `frameworks/api/auth_router.py` (nuevos); `.env`,
`.env.example` (editados) — ~180 líneas netas.

**Tests:** `tests/unit/inc1/test_iniciar_sesion_use_case.py`, `test_auth_controller.py`,
`test_jwt_pyjwt.py` (nuevos); `_fakes.py` (editado);
`tests/integration/inc1/test_auth_api_integration.py` (nuevo);
`test_usuario_repository_integration.py` (editado);
`tests/features/inc1/US-1.1.4-autenticacion-jwt.feature`,
`tests/step_defs/inc1/test_us_1_1_4_steps.py` (nuevos) — ~430 líneas.

**Documentación:** `docs/plans/inc1/US-1.1.4-{context,plan}.md`,
`docs/reports/inc1/US-1.1.4-report.md` (este archivo),
`quality/reports/inc1/US-1.1.4-{quality,coverage}.json`, `docs/traceability/matrix.md`
(editado), `CHANGELOG.md` (editado).

---

## Criterios de Aceptación

- [x] Login exitoso de Docente → JWT con claim `rol="docente"`, expiración 60 min, evento
  `SesionIniciada`
- [x] Login exitoso de Administrador → JWT con claim `rol="administrador"`
- [x] Login exitoso de Estudiante → JWT con claim `rol="estudiante"`
- [x] Rechazo por contraseña incorrecta → `CredencialesInvalidas`, mensaje que no distingue
  existencia del email
- [x] Rechazo por email inexistente → mismo `CredencialesInvalidas`, mismo mensaje
- [ ] Frontend: pantallas de login/error (`#login`, `#login-error`) — **diferido**, ver nota
  de alcance

**Criterios de backend cumplidos:** ✅ — frontend diferido con acuerdo explícito

---

## Próximos Pasos

- [ ] US-IEDD de infraestructura frontend (router + cliente API) + `Login.tsx`/
  `LoginError.tsx`/`Registro.tsx`/`RegistroExito.tsx`/`RegistroError.tsx`, diferida desde
  `US-1.1.2` y acumulada por cada US de Identidad desde entonces
- [ ] `US-1.1.5` (Issue #10) — autorización por rol (RBAC), última US-IEDD que RF-02 necesita
  para pasar a "Implementado" en `docs/traceability/matrix.md`
- [ ] Al cerrar `US-1.1.5`, revisar si conviene mover `IniciarSesionUseCase`/`AuthController`
  a un patrón compartido con el guard de autorización (dependency de FastAPI que valida JWT +
  rol por endpoint, según `ADR-007`)

---

## Lecciones Aprendidas

- 💡 Antes de crear un VO nuevo pedido por la spec, verificar si una propiedad ya existente
  en el aggregate (`Usuario.tipo_perfil`) cumple la misma función — evitó una envoltura
  redundante sobre `TipoPerfil`.
- 💡 Implementar un invariante de negocio (expiración del JWT) es la oportunidad natural de
  detectar y corregir configuración que había quedado desalineada con el ADR correspondiente
  (`ACCESS_TOKEN_EXPIRE_MINUTES` en 30 min desde el walking skeleton, vs. 60 min de
  `ADR-013`).
- ✅ Reutilizar el patrón exacto de una US-IEDD anterior del mismo BC (`RegistrarEstudianteUseCase`/
  `RegistroController` de `US-1.1.2`) redujo Fase 3 a una secuencia mecánica de 14 tareas sin
  decisiones de diseño pendientes.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-07-23
