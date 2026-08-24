# US-2.2.5: Usuario autenticado cambia su propia contraseña

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-2.2`
**Tipo**: `feat backend`
**Agregado principal afectado**: `Usuario`
**Bounded Context**: Identidad

---

## Descripcion (lenguaje de negocio)

Como **Usuario autenticado** (Administrador, Docente o Estudiante),
quiero **cambiar mi propia contraseña ingresando la actual y la nueva**
para **no depender del Administrador cuando simplemente quiero actualizarla (RF-19)**.

---

## Contexto del dominio

### Problema

RF-19 (elicitado 2026-07-17) cubre el caso self-service, distinto de `US-2.2.4` (mediado
por Administrador, para cuando el usuario ya no puede entrar). Comparte el campo
`bloqueada` de `Usuario` con `US-2.2.1`, pero con un contador de intentos fallidos propio e
independiente (`intentos_fallidos_password`) — fallar el cambio de contraseña tres veces
bloquea la cuenta igual que fallar el login tres veces, pero un fallo de un flujo no cuenta
para el otro.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Command | `CambiarPassword(usuario_id, password_actual, password_nueva)` | Verifica la actual y fija la nueva |
| Domain Event | `PasswordCambiada` | Señala el cambio exitoso |
| Domain Event | `CuentaBloqueada` | Se emite si este intento fallido llega al 3er consecutivo (mismo evento de `US-2.2.1`, origen distinto) |

---

## Especificacion del comportamiento

### Precondicion

- Actor autenticado con JWT válido (cualquier rol).
- `Usuario.bloqueada = false` — si ya está bloqueado, se rechaza sin intentar verificar
  `password_actual` (mismo criterio que `US-2.2.1` en login).

### Postcondicion

- `password_actual` verifica y `password_nueva` cumple INV-ID-11 → `password_hash`
  actualizado, `intentos_fallidos_password = 0`, evento `PasswordCambiada`. El JWT en curso
  sigue vigente (`ADR-013`, sin invalidación).
- `password_actual` no verifica y el contador (antes del intento) es `< 2` →
  `intentos_fallidos_password += 1`, se rechaza con `PasswordActualIncorrecta`.
- `password_actual` no verifica y el contador llega a 3 → `intentos_fallidos_password = 3`,
  `bloqueada = true`, se emite `CuentaBloqueada`, se rechaza con `PasswordActualIncorrecta`.

### Invariantes

| ID | Invariante |
|----|------------|
| INV-ID-10 | Contador de este flujo, independiente del de login; 3 fallos consecutivos bloquean la cuenta. |
| INV-ID-11 | `password_nueva` con mínimo 8 caracteres. |

---

## Criterios de aceptacion

```gherkin
Feature: Cambio de contraseña propio (US-2.2.5)

  Scenario: Cambio exitoso
    Given un Usuario autenticado con su contraseña actual correcta
    When ejecuta CambiarPassword(usuario_id, password_actual, "nuevaClave123")
    Then el sistema actualiza password_hash
    And intentos_fallidos_password vuelve a 0
    And se emite PasswordCambiada
    And el JWT en curso sigue siendo válido

  Scenario: Contraseña actual incorrecta, sin llegar al límite
    Given un Usuario con intentos_fallidos_password = 1
    When ejecuta CambiarPassword con la contraseña actual incorrecta
    Then intentos_fallidos_password pasa a 2
    And el sistema rechaza con PasswordActualIncorrecta

  Scenario: Tercer fallo consecutivo bloquea la cuenta
    Given un Usuario con intentos_fallidos_password = 2
    When ejecuta CambiarPassword con la contraseña actual incorrecta
    Then intentos_fallidos_password pasa a 3
    And bloqueada pasa a true
    And se emite CuentaBloqueada

  Scenario: Rechazo por contraseña nueva demasiado corta
    Given un Usuario autenticado con su contraseña actual correcta
    When ejecuta CambiarPassword con password_nueva de 5 caracteres
    Then el sistema rechaza con PasswordDemasiadoCorta

  Scenario: Cuenta ya bloqueada
    Given un Usuario con bloqueada = true
    When ejecuta CambiarPassword con cualquier dato
    Then el sistema rechaza con CuentaBloqueadaError sin verificar password_actual
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — se implementa con la arquitectura existente.

**Capa(s) afectadas:**
- [x] Entities — método `Usuario.cambiar_password(password_hash_actual_ok, password_hash_nuevo)`
  (o equivalente); nuevo error `PasswordActualIncorrecta`
- [x] Use Cases — `CambiarPasswordUseCase`
- [x] Interface Adapters — controller nuevo (`AutenticacionController` o extensión existente)
- [x] Frameworks — endpoint FastAPI `PUT /usuarios/me/password` (cualquier rol autenticado)
- [ ] Frontend — cubierto por `US-2.2.8`

---

## Fuente de verdad UX

No aplica a esta spec (backend puro) — las pantallas correspondientes (`#cambiar-password`,
`#cambiar-password-error`, `#cambiar-password-exito`) se especifican en `US-2.2.8`
(`docs/design/ux/wireframes-cuentas-administracion.md` §2.5-§2.7).

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/identidad/entities/usuario.py` | Método `cambiar_password(...)` — valida `password_nueva`, gestiona contador propio |
| `src/identidad/entities/errors.py` | Agregar `PasswordActualIncorrecta` (reutiliza `PasswordDemasiadoCorta` y `CuentaBloqueadaError` de `US-2.2.1`/`US-2.2.4`) |
| `src/identidad/entities/eventos.py` | Agregar `PasswordCambiada` |
| `src/identidad/use_cases/cambiar_password.py` | Orquesta el cambio, comparte el mecanismo de bloqueo con `IniciarSesion` sin duplicar lógica (método común en `Usuario` para evaluar el contador) |
| `src/identidad/interface_adapters/controllers/cuentas_controller.py` (o controller propio) | Endpoint `PUT /usuarios/me/password`, resuelve `usuario_id` desde el JWT |
| `src/identidad/frameworks/api/cuentas_router.py` | Ruta nueva |

---

## Referencias

- Relacionada con: `US-2.2.1` (mismo mecanismo de bloqueo, contador independiente),
  `US-2.2.4` (alternativa mediada por Administrador cuando ya no se puede entrar), `US-2.2.8`
  (frontend)
- Modelo de dominio: `docs/design/domain/BC-identidad-modelo.md` §3 "Diferidos", §11
  (RF-19 completo)
- Candidatas: `docs/plans/inc2/inc2-candidatas.md` §Iteración 2 — Backend

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
