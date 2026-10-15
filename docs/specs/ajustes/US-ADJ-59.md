# US-ADJ-59: Una cuenta deshabilitada no puede iniciar sesión

**Estado**: `Implementada` (2026-10-03) — PR pendiente de mergear
**Iteracion / Sprint**: `Incremento 7-ADJ — Ciclo de vida de la cuenta y ajustes de la UAT v1`
(decisión de Víctor, 2026-10-02: el 7-ADJ va antes de RF-07)
**Tipo**: `fix` backend + frontend
**Agregado principal afectado**: `Usuario`
**Bounded Context**: Identidad
**Origen**: UAT manual de cierre de alcance v1, hallazgo **#11** 🔴
(`quality/reports/uat/inc7/registro-hallazgos.md`, `plan-de-correccion.md` §3).

---

## Fuente de verdad UX

Solo la **Parte B (frontend)** la necesita, y **hoy no existe el artefacto aprobado**:
`docs/design/ux/wireframes-cuentas-administracion.md` §2.8 y el prototipo
`docs/design/ux/prototipos/identidad-cuentas-administracion.html` (`#login-bloqueada`) cubren
solo la cuenta bloqueada. Antes de tocar `frontend/` hay que agregar el estado
`#login-deshabilitada` (alerta + formulario deshabilitado, mismo patrón que `#login-bloqueada`) y
que Víctor lo apruebe (gate UX, `CLAUDE.md`). La **Parte A (backend)** no depende de esto y se
puede implementar y mergear antes.

---

## Descripcion (lenguaje de negocio)

Como **Administrador**,
quiero que **dar de baja una cuenta impida que esa persona vuelva a entrar al sistema**,
para **que la baja sea real y no solo un cambio de color en el listado**.

Como **persona con la cuenta dada de baja**,
quiero **ver un mensaje claro que me diga que mi cuenta fue deshabilitada**,
para **saber que tengo que hablar con un Administrador y no pensar que escribí mal la contraseña**.

---

## Contexto del dominio

### Problema (verificado en la UAT)

`Usuario.deshabilitada` solo se persiste y se usa para filtrar el listado de Cuentas
(`cuenta_query_repository.py`). Ni `IniciarSesionUseCase` ni el guard JWT lo consultan. Con
"Docente UAT7" dado de baja (fila y asignación a la Comisión conservadas, estado "Inactiva" en
el listado), por `curl`: `POST /identidad/login` con la contraseña correcta → **200 OK con token
válido** y `GET /materias` con ese token → **200**. La pantalla `EliminarCuenta.tsx` promete lo
contrario ("la cuenta se deshabilita… deja de poder iniciar sesión").

### Alcance del fix

**Parte A — Backend, BC Identidad:**

1. Error de dominio nuevo `CuentaDeshabilitadaError(usuario_id)` en `entities/errors.py`, mensaje
   "La cuenta está deshabilitada. Contactá a un administrador.".
2. `IniciarSesionUseCase.execute`: después de encontrar el `Usuario` y **antes** de mirar
   `bloqueada` y de verificar la contraseña, si `usuario.deshabilitada` lanza
   `CuentaDeshabilitadaError`. No incrementa `intentos_fallidos_login` ni persiste nada.
3. `auth_router.py`: mapea `CuentaDeshabilitadaError` a **403** con `detail` **estructurado**:
   `{"codigo": "cuenta_deshabilitada", "mensaje": "<texto del error>"}`. El `403` de cuenta
   bloqueada conserva su `detail` en texto plano (no se cambia un contrato ya testeado).

**Parte B — Frontend (bloqueada por el gate UX de arriba):**

4. `Login.tsx`: hoy **todo** `403` se interpreta como cuenta bloqueada. Pasa a discriminar por
   `err.detail.codigo`: `"cuenta_deshabilitada"` → nuevo componente
   `LoginCuentaDeshabilitadaError.tsx` ("Cuenta deshabilitada — Tu cuenta fue dada de baja.
   Contactá a un Administrador.") con el formulario deshabilitado (`fieldset`) como en el caso
   bloqueada; cualquier otro `403` conserva la alerta de bloqueada.

**Fuera de alcance:**
- **Revocar sesiones ya emitidas** y revalidar el estado en cada request (guard JWT,
  `src/shared`, `ADR-019`): descartado por la decisión 2 del plan de corrección — un JWT vive
  hasta 60 min sin blacklist (`ADR-013`), así que una baja corta el acceso en el próximo login,
  no al instante. Si molesta más adelante, revalidar en el guard se suma sin deshacer esto.
- Impedir `SolicitarRecuperacionPassword`/`ConfirmarNuevaPassword` sobre una cuenta
  deshabilitada: siguen igual (`INV-ID-17`); la contraseña cambia pero el login se rechaza igual.
- Que un Administrador deshabilite al último Administrador operativo: `US-ADJ-60`.

### Decisiones por defecto (a confirmar por Víctor)

1. **Error propio `403` + `detail` estructurado**, en vez de reutilizar el `401` de credenciales
   inválidas. Mejor para el usuario, y consistente con el precedente de `CuentaBloqueadaError`
   (que también se chequea antes de la contraseña). Costo: revela que esa cuenta existe y está
   deshabilitada a quien conozca el email — ya ocurre hoy con las bloqueadas. Alternativa: `401`
   genérico, que no filtra nada pero deja al usuario sin saber qué pasó y no necesita cambio de
   frontend.
2. **Se chequea antes de verificar la contraseña**, para que la respuesta no dependa de si era
   correcta ni consuma intentos.
3. **`deshabilitada` tiene prioridad sobre `bloqueada`** si ambas están en `true` (es la decisión
   manual del Administrador).

---

## Especificacion del comportamiento

### Precondicion

- Existe un `Usuario` con `deshabilitada = true` (por `EliminarCuentaUseCase` cuando tiene
  datos asociados, estabilización de portales 2026-09-09/10).
- Hoy ese `Usuario` puede iniciar sesión y recibir un JWT.

### Postcondicion

- `IniciarSesion` sobre una cuenta deshabilitada falla con `CuentaDeshabilitadaError` y **no
  emite JWT**, tanto con la contraseña correcta como con una incorrecta.
- El rechazo no modifica `intentos_fallidos_login` ni `bloqueada`.
- Al reactivar la cuenta (`activar()`) el login vuelve a funcionar sin otro paso.
- Cuentas no deshabilitadas: comportamiento idéntico al actual (login, bloqueo a los 3 fallos).

### Invariantes

- **INV-ID-18 (nueva):** una cuenta con `deshabilitada = true` no puede iniciar sesión, sin
  importar si la contraseña es correcta. El rechazo ocurre antes de verificar la contraseña y no
  consume intentos.

---

## Criterios de aceptacion

```gherkin
Feature: Una cuenta deshabilitada no puede iniciar sesión (US-ADJ-59)

  Scenario: Login con contraseña correcta sobre una cuenta deshabilitada
    Given un Usuario Docente con deshabilitada = true
    When se hace POST /identidad/login con su email y su contraseña correcta
    Then la respuesta es 403
    And el detail tiene codigo "cuenta_deshabilitada"
    And no se emite ningún JWT

  Scenario: El rechazo no depende de la contraseña ni consume intentos
    Given un Usuario con deshabilitada = true e intentos_fallidos_login = 0
    When se hace POST /identidad/login con una contraseña incorrecta
    Then la respuesta es 403 con codigo "cuenta_deshabilitada"
    And intentos_fallidos_login sigue en 0
    And bloqueada sigue en false

  Scenario: Reactivar la cuenta restituye el acceso
    Given un Usuario que estuvo deshabilitado y fue reactivado con activar()
    When se hace POST /identidad/login con su email y su contraseña correcta
    Then la respuesta es 200 con un JWT válido

  Scenario: Deshabilitada y bloqueada a la vez
    Given un Usuario con deshabilitada = true y bloqueada = true
    When se hace POST /identidad/login con su email
    Then la respuesta es 403 con codigo "cuenta_deshabilitada"

  Scenario: Una cuenta activa no cambia de comportamiento
    Given un Usuario con deshabilitada = false y bloqueada = false
    When se hace POST /identidad/login con su email y su contraseña correcta
    Then la respuesta es 200 con un JWT válido

  Scenario: Una cuenta bloqueada conserva su respuesta actual
    Given un Usuario con bloqueada = true y deshabilitada = false
    When se hace POST /identidad/login
    Then la respuesta es 403 con el detail en texto plano de cuenta bloqueada

  Scenario: El login muestra la alerta de cuenta deshabilitada (frontend, tras el gate UX)
    Given estoy en /login
    When ingreso las credenciales de una cuenta deshabilitada
    Then veo la alerta "Cuenta deshabilitada"
    And el formulario queda deshabilitado
    And no veo la alerta de "Cuenta bloqueada"
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] Sí
- [x] No — agrega una guarda a un use case existente y un error de dominio; no cambia puertos
  ni dependencias entre BC.

**Capa(s) afectadas:**
- [x] Entities — `CuentaDeshabilitadaError`
- [x] Use Cases — `IniciarSesionUseCase` (sin dependencias nuevas: el riesgo de CBO es nulo)
- [x] Interface Adapters — `auth_router.py` (mapeo a 403 estructurado)
- [x] Frontend — `Login.tsx`, `LoginCuentaDeshabilitadaError.tsx` (Parte B, tras el gate UX)

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/identidad/entities/errors.py` | `CuentaDeshabilitadaError` |
| `src/identidad/use_cases/iniciar_sesion.py` | Guarda de `deshabilitada` antes de `bloqueada` y de la contraseña; docstring |
| `src/identidad/frameworks/api/auth_router.py` | Mapeo a `403` con `detail` estructurado |
| tests unit/integration/BDD (patrón de `inc5-adj`/`inc6-adj`: `tests/integration/inc7-adj/`, `tests/features/inc7-adj/US-ADJ-59-*.feature`) | Tests de los escenarios de arriba |
| `frontend/src/pages/identidad/Login.tsx`, `LoginCuentaDeshabilitadaError.tsx` (+ tests) | Discriminar por `detail.codigo` (Parte B) |
| `docs/design/domain/BC-identidad-modelo.md` | §3 error de `IniciarSesion`; §4 `Usuario` — agregar `deshabilitada` (hoy **no figura** en la tabla de atributos) e `INV-ID-18` |
| `docs/design/ux/wireframes-cuentas-administracion.md` + prototipo | Estado `#login-deshabilitada` (gate UX) |

---

## Referencias

- Incremento: 7-ADJ — `docs/plans/inc7-adj/inc7-adj-candidatas.md`
- `quality/reports/uat/inc7/plan-de-correccion.md` §3 (`US-ADJ-59`), §7 decisión 2
- `quality/reports/uat/inc7/registro-hallazgos.md` hallazgo #11
- `docs/adr/ADR-013` (JWT 60 min sin refresh ni blacklist), `ADR-019` (JWT/RBAC en `shared/`)
- Issue: [#474](https://github.com/vvalotto/cognion/issues/474)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
