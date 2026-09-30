# US-ADJ-39: Confirmar nueva contraseña con token de recuperación (endpoint público)

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 5-ADJ — Identidad Autoservicio y Analytics del Docente`,
Iteración 2
**Tipo**: `feature` (backend nuevo, endpoint público)
**Bounded Context**: Identidad
**Origen**: `docs/plans/inc5-adj/inc5-adj-candidatas.md` §Iteración 2. Modelo aprobado:
`docs/design/domain/BC-identidad-modelo.md` §13.2/13.3/13.4 (`US-ADJ-32`). Depende de
`US-ADJ-38` (necesita que el token ya se pueda generar).

---

## Fuente de verdad UX

`docs/design/ux/wireframes-identidad-autoservicio.md` §4.3 ("Recuperar — definir nueva
contraseña"), §4.4 ("Recuperar — link vencido/inválido/ya usado") y §4.5 ("Recuperar —
éxito"). Prototipo navegable: `docs/design/ux/prototipos/identidad-autoservicio.html`
(`#recuperar-nueva`, `#recuperar-token-invalido`, `#recuperar-exito`). Sin pantalla propia
todavía — esta US es backend puro (`US-ADJ-40` construye las pantallas).

---

## Descripcion (lenguaje de negocio)

Como **quien recibió un email de recuperación de contraseña**,
quiero **definir una contraseña nueva usando el link recibido**
para **recuperar el acceso a mi cuenta sin necesitar la contraseña anterior**.

---

## Contexto del dominio

### Problema

`US-ADJ-38` genera el token y dispara el email, pero no existe todavía ningún mecanismo para
canjear ese token por una contraseña nueva.

### Alcance del fix

**Backend nuevo**, BC Identidad:

1. Comando `ConfirmarNuevaPassword(token, password_nueva)` →
   `ConfirmarNuevaPasswordUseCase`:
   - Busca el `TokenRecuperacionPassword` por `token`. Si no existe → `TokenRecuperacionInvalido`.
   - Si `usado_en is not None` → `TokenRecuperacionYaUsado`.
   - Si `expira_en` ya pasó (INV-ID-13) → `TokenRecuperacionVencido`.
   - Si el token es válido: aplica `Usuario.validar_password_nueva(password_nueva)` (INV-ID-11
     ampliada, `US-ADJ-36`) — mismas excepciones `PasswordDemasiadoCorta`/
     `PasswordSinComplejidadSuficiente` que ya lanzan `CambiarPassword`/`ResetearPassword`.
   - Si la contraseña es válida: hashea, actualiza `Usuario.password_hash` (mismo método que
     `resetear_password()` de `US-2.2.4`, sin tocar `bloqueada` ni los contadores de intentos
     fallidos — nota de diseño explícita en `wireframes-identidad-autoservicio.md` §3.1: una
     cuenta bloqueada sigue bloqueada tras este flujo), marca `usado_en` en el token, persiste
     ambos cambios en una sola transacción, y emite `PasswordRecuperada`.
2. Endpoint nuevo `POST /identidad/recuperar-password/confirmar` (público) — body `{token,
   password_nueva}`, responde `200 OK` con `PasswordRecuperada` en éxito, o el status/detail
   correspondiente a cada excepción (mismo criterio de mapeo error→status ya usado en el resto
   del BC: 404/410/409 o 422 según corresponda — a definir con el patrón existente de
   `frameworks/api/`).

**Fuera de alcance de esta US:**
- Generar el token — `US-ADJ-38`.
- Cualquier pantalla — `US-ADJ-40`.
- Desbloquear la cuenta o resetear contadores de intentos fallidos — explícitamente fuera,
  ver nota de diseño arriba.

---

## Especificacion del comportamiento

### Precondicion

- Existe un `TokenRecuperacionPassword` generado por `US-ADJ-38`, potencialmente vigente,
  vencido, o ya usado.
- No existe ningún endpoint para canjear ese token.

### Postcondicion

- Un token vigente y sin usar, junto con una `password_nueva` que cumple INV-ID-11 ampliada,
  actualiza `Usuario.password_hash` y marca el token como usado.
- Un token vencido, inválido, o ya usado no modifica nada y responde con el error específico.
- Una `password_nueva` que no cumple INV-ID-11 no modifica nada, aunque el token sea válido.
- El mismo token no puede canjearse dos veces.
- El estado `bloqueada`/contadores de intentos fallidos de `Usuario` no cambia por este flujo.

### Invariantes

- **INV-ID-11 (ampliada):** `password_nueva` debe cumplir mínimo 12 caracteres + mayúscula +
  número + símbolo.
- **INV-ID-13:** un token vencido se rechaza, sin excepción.

---

## Criterios de aceptacion

```gherkin
Feature: Confirmar nueva contraseña con token de recuperación (US-ADJ-39)

  Scenario: Confirmar con un token vigente y contraseña válida
    Given un TokenRecuperacionPassword vigente y sin usar
    And una password_nueva que cumple INV-ID-11 ampliada
    When se hace POST /identidad/recuperar-password/confirmar con ese token y esa password
    Then la respuesta es 200 OK
    And Usuario.password_hash queda actualizado
    And el token queda marcado como usado

  Scenario: Confirmar con un token ya usado
    Given un TokenRecuperacionPassword ya usado
    When se hace POST /identidad/recuperar-password/confirmar con ese token
    Then la respuesta es un error TokenRecuperacionYaUsado
    And Usuario.password_hash no cambia

  Scenario: Confirmar con un token vencido
    Given un TokenRecuperacionPassword cuya expira_en ya pasó
    When se hace POST /identidad/recuperar-password/confirmar con ese token
    Then la respuesta es un error TokenRecuperacionVencido

  Scenario: Confirmar con un token inexistente
    Given ningún TokenRecuperacionPassword tiene el token dado
    When se hace POST /identidad/recuperar-password/confirmar con ese token
    Then la respuesta es un error TokenRecuperacionInvalido

  Scenario: Confirmar con una contraseña que no cumple la política
    Given un TokenRecuperacionPassword vigente y sin usar
    And una password_nueva de menos de 12 caracteres
    When se hace POST /identidad/recuperar-password/confirmar con ese token y esa password
    Then la respuesta es un error PasswordDemasiadoCorta
    And el token sigue sin usar

  Scenario: Confirmar no desbloquea una cuenta bloqueada
    Given un Usuario bloqueado con un TokenRecuperacionPassword vigente
    When se confirma una contraseña nueva válida con ese token
    Then Usuario.password_hash queda actualizado
    And Usuario.bloqueada sigue en true
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] Sí
- [x] No — reutiliza `Usuario.validar_password_nueva()`/`resetear_password()` y el mapeo
  error→status ya existentes; el aggregate y el puerto de `TokenRecuperacionPassword` ya se
  crearon en `US-ADJ-38`.

**Capa(s) afectadas:**
- [x] Entities — `TokenRecuperacionPassword.marcar_usado()` (o equivalente), sin cambios en `Usuario`
- [x] Use Cases — `ConfirmarNuevaPasswordUseCase`
- [x] Interface Adapters — endpoint nuevo, mapeo de excepciones a status HTTP

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/identidad/entities/token_recuperacion_password.py` | Método de mutación para marcar el token usado + validaciones de vencimiento/uso |
| `src/identidad/entities/errors.py` (o equivalente) | Excepciones `TokenRecuperacionVencido`, `TokenRecuperacionInvalido`, `TokenRecuperacionYaUsado` |
| `src/identidad/use_cases/confirmar_nueva_password.py` | Use case nuevo |
| `src/identidad/interface_adapters/controllers/` | Endpoint `POST /identidad/recuperar-password/confirmar` |

---

## Referencias

- Incremento: 5-ADJ
- `docs/plans/inc5-adj/inc5-adj-candidatas.md` §Iteración 2
- `docs/design/domain/BC-identidad-modelo.md` §13.2, §13.3, §13.4
- `docs/design/ux/wireframes-identidad-autoservicio.md` §4.3, §4.4, §4.5
- Issue: [#340](https://github.com/vvalotto/cognion/issues/340)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
