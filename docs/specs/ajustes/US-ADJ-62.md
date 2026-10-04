# US-ADJ-62: Recuperar la contraseña por autoservicio también desbloquea la cuenta

**Estado**: `Parte A (backend) implementada 2026-10-04`; Parte B (frontend) pendiente del gate UX
**Iteracion / Sprint**: `Incremento 7-ADJ — Ciclo de vida de la cuenta y ajustes de la UAT v1`
(decisión de Víctor, 2026-10-02: recuperar la contraseña **sí desbloquea**, plan de corrección §7
decisión 4)
**Tipo**: `fix` backend + copy de frontend
**Agregado principal afectado**: `Usuario`
**Bounded Context**: Identidad
**Origen**: UAT manual de cierre de alcance v1, hallazgo **#5** 🟡
(`quality/reports/uat/inc7/registro-hallazgos.md`, `plan-de-correccion.md` §3).
**Reabre una decisión previa:** `US-ADJ-39` dejó explícito que este flujo "no desbloquea la
cuenta" (y `wireframes-identidad-autoservicio.md` §3.1 lo fijó como nota de diseño). Esa decisión
se **revierte** acá; hay que actualizar esos artefactos, no solo el código.
**Interactúa con**: `US-ADJ-60` (bloqueo temporal del último Administrador) y `US-ADJ-59`.

---

## Fuente de verdad UX

Solo el texto de la alerta de cuenta bloqueada necesita cambio, y **hoy ese texto es el aprobado
con la regla anterior**: `docs/design/ux/prototipos/identidad-cuentas-administracion.html`
(`#login-bloqueada`) y `wireframes-cuentas-administracion.md` §2.8 mandan al usuario a "Contactar
a un Administrador para restablecer tu contraseña", sin ofrecer la recuperación por email. El
copy nuevo hay que actualizarlo en el prototipo y que Víctor lo apruebe antes de tocar
`LoginCuentaBloqueadaError.tsx` (gate UX). La **Parte A (backend)** no depende de esto.

---

## Descripcion (lenguaje de negocio)

Como **usuario que se bloqueó por equivocarse con la contraseña**,
quiero que **recuperarla con el link que me llega por email también me desbloquee**,
para **volver a entrar sin depender de que un Administrador me destrabe**.

---

## Contexto del dominio

### Problema (vivido en la UAT)

Una cuenta se bloquea a los 3 intentos fallidos. El usuario hace todo el recorrido de "Olvidé mi
contraseña": pide el link, abre el email, define una contraseña nueva y el sistema dice que
quedó actualizada. Al intentar entrar, **sigue bloqueada**. Quien abrió el link del email ya
demostró controlar la cuenta, que es el mismo control que se exige para el reseteo del
Administrador (`US-2.2.4`), y ese sí desbloquea. Con un único Administrador, además, cada
bloqueo de un Docente o Estudiante termina en su bandeja.

### Alcance del fix

**Parte A — Backend, BC Identidad:**

1. `Usuario.recuperar_password(password_hash_nuevo)` pasa a comportarse igual que
   `resetear_password`: fija el hash, `bloqueada = false`, `intentos_fallidos_login = 0`,
   `intentos_fallidos_password = 0` y, si existe (`US-ADJ-60`), `bloqueada_hasta = NULL`. Devuelve
   `True` si la cuenta estaba bloqueada. Se implementa delegando en `resetear_password` para no
   duplicar la lógica (hoy son dos métodos distintos solo por esta diferencia).
2. `ConfirmarNuevaPasswordUseCase.execute` devuelve además un
   `CuentaDesbloqueada | None` (mismo patrón que `ResetearPasswordUseCase`): se emite solo si la
   cuenta estaba bloqueada. Actualizar el docstring de `CuentaDesbloqueada` ("tras un reseteo **o
   una recuperación** de contraseña").
3. **No** toca `deshabilitada`: recuperar la contraseña **no reactiva** una cuenta dada de baja.
   Con `US-ADJ-59` esa cuenta sigue sin poder iniciar sesión.
4. El endpoint `POST /identidad/recuperar-password/confirmar` no cambia de contrato ni de
   status; solo cambia el estado que deja en el `Usuario`. Actualizar el docstring del router
   (hoy dice "No desbloquea la cuenta ni resetea sus contadores de intentos fallidos").

**Parte B — Frontend (bloqueada por el gate UX):**

5. `LoginCuentaBloqueadaError.tsx`: el texto pasa a ofrecer también la recuperación por email
   ("…podés recuperar tu contraseña por email o pedirle a un Administrador que la restablezca"),
   con el link a `/recuperar-password`. Para la cuenta bloqueada por `US-ADJ-60`
   (`cuenta_bloqueada_temporal`) el copy lo define esa US.

**Actualizar artefactos que hoy afirman lo contrario:**
- `docs/specs/ajustes/US-ADJ-39.md`: el escenario "Confirmar no desbloquea una cuenta bloqueada"
  y la postcondición "El estado `bloqueada`/contadores … no cambia por este flujo" pasan a la
  regla nueva, con una nota "Enmendada por `US-ADJ-62`".
- `tests/features/inc5-adj/US-ADJ-39-confirmar-recuperacion-password.feature` y
  `tests/step_defs/inc5-adj/test_us_adj_39_steps.py`: hoy afirman `bloqueada` sigue en `true`.
- `docs/design/ux/wireframes-identidad-autoservicio.md` §3.1 (nota de diseño, líneas ~67-69) y
  §"Fuera de alcance" (~217): "una cuenta bloqueada sigue sin poder loguearse aunque recupere su
  contraseña".
- Docstrings de `Usuario.recuperar_password`, `ConfirmarNuevaPasswordUseCase` y
  `recuperacion_password_router.py`.

**Fuera de alcance:**
- Reactivar cuentas `deshabilitadas` por recuperación (decisión manual del Administrador).
- Cambiar la generación o la vigencia del token (`US-ADJ-38`).
- Enviar un email de aviso de desbloqueo.

---

## Especificacion del comportamiento

### Precondicion

- Una cuenta con `bloqueada = true` (por 3 fallos de login o de cambio de contraseña) y un
  `TokenRecuperacionPassword` vigente.
- Hoy canjear el token cambia el hash pero deja `bloqueada = true` y los contadores intactos.

### Postcondicion

- Canjear un token vigente con una contraseña válida deja `bloqueada = false`,
  `intentos_fallidos_login = 0`, `intentos_fallidos_password = 0` y `bloqueada_hasta = NULL`.
- Se emite `CuentaDesbloqueada` solo si la cuenta estaba bloqueada.
- Una cuenta no bloqueada: comportamiento sin cambios (solo cambia el hash).
- Un token inválido, vencido o usado, o una contraseña que no cumple `INV-ID-11`, no cambia nada
  (incluido el bloqueo).
- Una cuenta `deshabilitada` no se reactiva.

### Invariantes

- **INV-ID-11 (ampliada), INV-ID-13:** sin cambios.
- **Enmienda a `INV-ID-10`:** el bloqueo por intentos fallidos se levanta con un reseteo de
  contraseña por un Administrador **o con una recuperación de contraseña por email**.

---

## Criterios de aceptacion

```gherkin
Feature: Recuperar la contraseña desbloquea la cuenta (US-ADJ-62)

  Scenario: Recuperar la contraseña desbloquea una cuenta bloqueada por intentos fallidos
    Given un Usuario con bloqueada = true e intentos_fallidos_login = 3
    And un TokenRecuperacionPassword vigente de ese Usuario
    When se confirma una contraseña nueva válida con ese token
    Then Usuario.password_hash queda actualizado
    And Usuario.bloqueada es false
    And intentos_fallidos_login e intentos_fallidos_password son 0
    And se emite CuentaDesbloqueada

  Scenario: Tras recuperar, el usuario puede iniciar sesión con la contraseña nueva
    Given un Usuario bloqueado que recuperó su contraseña
    When se hace POST /identidad/login con su email y la contraseña nueva
    Then la respuesta es 200 con un JWT válido

  Scenario: Recuperar la contraseña libera al último Administrador bloqueado temporalmente
    Given el único Administrador con bloqueada = true y bloqueada_hasta en el futuro
    When confirma una contraseña nueva válida con un token vigente
    Then queda con bloqueada = false y bloqueada_hasta = NULL

  Scenario: Una cuenta no bloqueada no emite desbloqueo
    Given un Usuario con bloqueada = false y un token vigente
    When se confirma una contraseña nueva válida
    Then el hash queda actualizado
    And no se emite CuentaDesbloqueada

  Scenario: Recuperar la contraseña no reactiva una cuenta deshabilitada
    Given un Usuario con deshabilitada = true y un token vigente
    When se confirma una contraseña nueva válida
    Then deshabilitada sigue en true
    And el login responde 403 con codigo "cuenta_deshabilitada"

  Scenario: Un token inválido no desbloquea nada
    Given un Usuario bloqueado
    When se confirma una contraseña con un token vencido
    Then la respuesta es un error TokenRecuperacionVencido
    And bloqueada sigue en true

  Scenario: Una contraseña que no cumple la política no desbloquea
    Given un Usuario bloqueado con un token vigente
    When se confirma una contraseña de menos de 12 caracteres
    Then la respuesta es un error PasswordDemasiadoCorta
    And bloqueada sigue en true
    And el token sigue sin usar

  Scenario: La alerta de cuenta bloqueada ofrece la recuperación por email (frontend, tras el gate UX)
    Given estoy en /login con una cuenta bloqueada
    Then veo la alerta "Cuenta bloqueada"
    And veo un link a la recuperación de contraseña
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] Sí
- [x] No — cambia una regla de `Usuario` y un valor de retorno; no toca puertos ni otros BC.
  Sí **revierte una decisión de `US-ADJ-39`**, que debe quedar anotada en esa spec.

**Capa(s) afectadas:**
- [x] Entities — `Usuario.recuperar_password`, docstring de `CuentaDesbloqueada`
- [x] Use Cases — `ConfirmarNuevaPasswordUseCase` (retorno con el evento opcional)
- [x] Interface Adapters — controller de recuperación y docstring del router
- [x] Frontend — `LoginCuentaBloqueadaError.tsx` (copy, tras el gate UX)

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/identidad/entities/usuario.py` | `recuperar_password` delega en `resetear_password`; devuelve si estaba bloqueada |
| `src/identidad/entities/eventos.py` | Docstring de `CuentaDesbloqueada` |
| `src/identidad/use_cases/confirmar_nueva_password.py` | Emite `CuentaDesbloqueada \| None`; docstring |
| `src/identidad/interface_adapters/controllers/recuperacion_password_controller.py` | Adaptar al nuevo retorno |
| `src/identidad/frameworks/api/recuperacion_password_router.py` | Docstring (contrato HTTP sin cambios) |
| `tests/features/inc5-adj/US-ADJ-39-*.feature`, `tests/step_defs/inc5-adj/test_us_adj_39_steps.py` | Cambiar el escenario que afirma "sigue bloqueada" |
| tests nuevos de este incremento | Escenarios de arriba (patrón `inc5-adj`/`inc6-adj`) |
| `docs/specs/ajustes/US-ADJ-39.md` | Nota "Enmendada por US-ADJ-62" y escenario/postcondición |
| `docs/design/ux/wireframes-identidad-autoservicio.md` | §3.1 y "Fuera de alcance": quitar la regla anterior |
| `docs/design/domain/BC-identidad-modelo.md` | Enmienda a `INV-ID-10` |
| `frontend/src/pages/identidad/LoginCuentaBloqueadaError.tsx` (+ test) | Copy con la recuperación por email (Parte B) |
| `docs/design/ux/wireframes-cuentas-administracion.md` §2.8 + prototipo | Copy de `#login-bloqueada` (gate UX) |

---

## Referencias

- Incremento: 7-ADJ — `docs/plans/inc7-adj/inc7-adj-candidatas.md`
- `quality/reports/uat/inc7/plan-de-correccion.md` §3 (`US-ADJ-62`), §7 decisión 4
- `quality/reports/uat/inc7/registro-hallazgos.md` hallazgo #5
- `docs/specs/ajustes/US-ADJ-39.md` (decisión que se revierte), `US-ADJ-38`, `US-2.2.4`
- Issue: [#477](https://github.com/vvalotto/cognion/issues/477)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
