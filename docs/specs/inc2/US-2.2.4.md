# US-2.2.4: Administrador resetea la contraseña de una cuenta (desbloqueo incluido)

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-2.2`
**Tipo**: `feat backend`
**Agregado principal afectado**: `Usuario`
**Bounded Context**: Identidad

---

## Descripcion (lenguaje de negocio)

Como **Administrador**,
quiero **resetear la contraseña de una cuenta**
para **resolver tanto un pedido de recuperación como una cuenta bloqueada, sin que el
docente tenga que intervenir (RF-03)**.

---

## Contexto del dominio

### Problema

Ya modelado en `BC-identidad-modelo.md` §3/§9 como comando diferido. Es **la única** forma
de desbloquear una cuenta — no existe un comando `DesbloquearCuenta` separado, porque
recuperación y desbloqueo son, en la práctica, la misma necesidad del usuario ("no puedo
entrar, necesito una contraseña nueva").

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Command | `ResetearPassword(usuario_id, password_nueva, administrador_id)` | Fija una contraseña nueva y desbloquea si corresponde |
| Domain Event | `PasswordReseteada` | Señala el cambio de contraseña |
| Domain Event | `CuentaDesbloqueada` | Se emite solo si la cuenta estaba `bloqueada = true` |

---

## Especificacion del comportamiento

### Precondicion

- Actor autenticado con JWT válido y claim `rol = administrador`.
- `Usuario` (`usuario_id`) existe.
- `password_nueva` tiene al menos 8 caracteres (INV-ID-11).

### Postcondicion

- `Usuario.password_hash` actualizado (bcrypt, `ADR-014`).
- `Usuario.bloqueada = false`, `intentos_fallidos_login = 0`,
  `intentos_fallidos_password = 0` — independientemente de si estaba bloqueada o no (reseteo
  también limpia contadores de una cuenta activa, evita que un fallo previo cercano al límite
  quede "arrastrado").
- Evento `PasswordReseteada`; además `CuentaDesbloqueada` si `bloqueada` era `true` antes del
  reseteo.
- El JWT de una sesión previa de ese usuario, si existiera una activa, no se invalida —
  mismo criterio stateless de `ADR-013` (sin blacklist).

### Invariantes

| ID | Invariante |
|----|------------|
| INV-ID-11 | Toda contraseña nueva tiene un mínimo de 8 caracteres. |

---

## Criterios de aceptacion

```gherkin
Feature: Administrador resetea contraseña y desbloquea (US-2.2.4)

  Scenario: Reseteo de cuenta bloqueada
    Given un Usuario con bloqueada = true
    When un Administrador ejecuta ResetearPassword(usuario_id, "nuevaClave123", administrador_id)
    Then el sistema actualiza password_hash
    And bloqueada pasa a false, los contadores vuelven a 0
    And se emiten PasswordReseteada y CuentaDesbloqueada

  Scenario: Reseteo de cuenta activa (no bloqueada)
    Given un Usuario con bloqueada = false
    When un Administrador ejecuta ResetearPassword(usuario_id, "nuevaClave123", administrador_id)
    Then el sistema actualiza password_hash
    And se emite PasswordReseteada, sin CuentaDesbloqueada

  Scenario: Rechazo por contraseña demasiado corta
    Given un Usuario existente
    When un Administrador ejecuta ResetearPassword(usuario_id, "corta", administrador_id)
    Then el sistema rechaza con PasswordDemasiadoCorta
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — se implementa con la arquitectura existente.

**Capa(s) afectadas:**
- [x] Entities — método `Usuario.resetear_password(password_hash_nuevo)`; nuevo error
  `PasswordDemasiadoCorta`
- [x] Use Cases — `ResetearPasswordUseCase`
- [x] Interface Adapters — endpoint nuevo en `CuentasController`
- [x] Frameworks — endpoint FastAPI `POST /usuarios/{id}/resetear-password` (rol `administrador`)
- [ ] Frontend — cubierto por `US-2.2.7`

---

## Fuente de verdad UX

No aplica a esta spec (backend puro) — las pantallas correspondientes (`#cuenta-resetear`,
`#cuenta-reseteada`) se especifican en `US-2.2.7`
(`docs/design/ux/wireframes-cuentas-administracion.md` §2.3, §2.4).

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/identidad/entities/usuario.py` | Método `resetear_password(password_hash_nuevo)` — valida longitud, resetea `bloqueada` y contadores |
| `src/identidad/entities/errors.py` | Agregar `PasswordDemasiadoCorta` |
| `src/identidad/entities/eventos.py` | Agregar `PasswordReseteada`, `CuentaDesbloqueada` |
| `src/identidad/use_cases/resetear_password.py` | Orquesta el reseteo, decide si emite `CuentaDesbloqueada` |
| `src/identidad/interface_adapters/controllers/cuentas_controller.py` | Endpoint de reseteo |
| `src/identidad/frameworks/api/cuentas_router.py` | `POST /usuarios/{id}/resetear-password` |

---

## Referencias

- Relacionada con: `US-2.2.1` (campos que este comando resetea), `US-2.2.3` (detalle desde
  donde se dispara), `US-2.2.7` (frontend)
- Modelo de dominio: `docs/design/domain/BC-identidad-modelo.md` §3 "Diferidos", §9 punto 3
  (RF-03, recuperación mediada por Administrador)
- Candidatas: `docs/plans/inc2/inc2-candidatas.md` §Iteración 2 — Backend

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
