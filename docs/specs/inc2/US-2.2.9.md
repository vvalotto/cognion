# US-2.2.9: Login refleja el estado de cuenta bloqueada (UI)

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-2.2`
**Tipo**: `feat frontend`
**Agregado principal afectado**: — (consume `US-2.2.1`, sin lógica de dominio propia en el frontend)
**Bounded Context**: Identidad

---

## Descripcion (lenguaje de negocio)

Como **Usuario** que intenta iniciar sesión con una cuenta bloqueada,
quiero **ver un mensaje explícito que me diga que mi cuenta está bloqueada y qué hacer**
para **no confundirlo con un simple error de contraseña incorrecta**.

---

## Contexto del dominio

### Problema

`US-2.2.1` extiende `IniciarSesion` para lanzar `CuentaBloqueadaError` cuando
`Usuario.bloqueada = true`, pero el `Login.tsx` de `US-1.1.6`/`US-1.1.7` solo maneja el caso
genérico `CredencialesInvalidas` (`wireframes-identidad.md` §2.2). Esta US agrega el manejo
específico del nuevo caso de error, sin tocar el resto del flujo de login.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Endpoint consumido | `POST /auth/login` | Ya existe, extendido en `US-2.2.1` para devolver 403 en cuenta bloqueada |

---

## Especificacion del comportamiento

### Precondicion

- `US-2.2.1` implementada (el backend distingue `CuentaBloqueadaError` de
  `CredencialesInvalidas`).

### Postcondicion

- Login rechazado por `CredencialesInvalidas` → comportamiento sin cambios de
  `US-1.1.7` (mensaje genérico).
- Login rechazado por cuenta bloqueada (403 con el código específico) → la pantalla muestra
  la alerta de "Cuenta bloqueada" (`wireframes-cuentas-administracion.md` §2.8), deshabilita
  los campos y el botón "Ingresar", y dirige a contactar a un Administrador.

### Invariantes

| ID | Invariante |
|----|------------|
| — | N/A — el frontend solo distingue la respuesta del backend, sin lógica de dominio propia. |

---

## Criterios de aceptacion

```gherkin
Feature: Login refleja cuenta bloqueada (US-2.2.9)

  Scenario: Intento de login sobre cuenta bloqueada
    Given un Usuario con su cuenta bloqueada
    When intenta iniciar sesión con cualquier contraseña
    Then el sistema muestra la alerta "Cuenta bloqueada"
    And deshabilita el formulario de login

  Scenario: Login con credenciales inválidas en cuenta no bloqueada (sin regresión)
    Given un Usuario con su cuenta activa
    When intenta iniciar sesión con una contraseña incorrecta
    Then el sistema muestra el mensaje genérico de US-1.1.7, sin mencionar bloqueo
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — extiende el manejo de errores de un flujo ya implementado.

**Capa(s) afectadas:**
- [x] Frontend — `frontend/src/lib/auth-api.ts` (distingue el código de error nuevo),
  `frontend/src/pages/Login.tsx`
- [ ] Backend — sin cambios (ya cubierto por `US-2.2.1`)

---

## Fuente de verdad UX

`docs/design/ux/wireframes-cuentas-administracion.md` §2.8 (`#login-bloqueada`), extiende
`docs/design/ux/wireframes-identidad.md` §2.2. Prototipo navegable:
`docs/design/ux/prototipos/identidad-cuentas-administracion.html`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/lib/auth-api.ts` | Distinguir el código de error de cuenta bloqueada de `CredencialesInvalidas` |
| `frontend/src/pages/Login.tsx` | Nueva rama de error: alerta específica + formulario deshabilitado |

---

## Referencias

- Relacionada con: `US-2.2.1` (backend), `US-1.1.7` (manejo de error de login existente, no
  se modifica, solo se extiende)
- Candidatas: `docs/plans/inc2/inc2-candidatas.md` §Iteración 2 — Frontend

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
