# US-1.1.8: Estudiante se registra desde la UI con un link de invitación

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-1.2`
**Tipo**: `feat frontend`
**Agregado principal afectado**: — (consume `POST /identidad/registro`, sin lógica de dominio propia en el frontend)
**Bounded Context**: Identidad

---

## Descripcion (lenguaje de negocio)

Como **Estudiante** que recibió un link de invitación por email,
quiero **completar mi registro desde una pantalla web**
para **quedar asignado automáticamente a mi comisión sin aprobación del docente (RF-01)**.

---

## Contexto del dominio

### Problema

`POST /identidad/registro` está implementado y probado desde `US-1.1.2`/`US-1.1.3` (incluida
la distinción de rechazo por token inexistente, vencido o ya usado), pero no hay ninguna
pantalla que lo consuma. El email que envía `US-1.1.1` (`GenerarInvitacion`) apunta a una URL
con el token — sin esta US, ese link no lleva a ningún lado.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Endpoint consumido | `POST /identidad/registro` | Ya existe (`US-1.1.2`, `US-1.1.3`) — recibe `token`/`nombre`/`email`/`password`, devuelve el Usuario creado (201) o 422 (`InvitacionInvalida`/`InvitacionVencida`/`InvitacionYaUsada`)/409 (`EmailYaRegistrado`) |
| Cliente API | `api-client.ts` | Ya existe (`US-1.1.6`) |

---

## Especificacion del comportamiento

### Precondicion

- `US-1.1.6` implementada.
- La URL de registro incluye el token de invitación como query param (`/registro?token=...`),
  coherente con el link que `US-1.1.1` envía por email.

### Postcondicion

- Token vigente + datos válidos → `POST /identidad/registro` devuelve 201, se muestra
  `RegistroExito.tsx`. El Estudiante **no** queda autenticado automáticamente (coherente con
  el backend, `US-1.1.2`) — debe ir a `/login` (`US-1.1.7`) para iniciar sesión.
- Token inexistente, vencido o ya usado (422) → se muestra `RegistroError.tsx` con un mensaje
  genérico, sin distinguir el motivo entre los tres casos.
- Email ya registrado (409) → se muestra el error en el propio formulario de `Registro.tsx`
  (no es un problema del token, es un dato del formulario — el Estudiante puede corregir el
  email e reintentar).

### Invariantes

| ID | Invariante |
|----|------------|
| — | La UI no distingue el motivo del rechazo entre `InvitacionInvalida`, `InvitacionVencida` e `InvitacionYaUsada` — mismo criterio de "sin recuperación automática" del backend (`ADR-012`, `US-1.1.3`). |
| — | El Estudiante nunca queda autenticado automáticamente tras el registro (INV-ID-05 se satisface en el backend; la UI solo refleja que no hay JWT en la respuesta). |

---

## Criterios de aceptacion

```gherkin
Feature: Registro desde la UI (US-1.1.8)

  Scenario: Registro exitoso con invitación vigente
    Given una URL de registro con un token vigente
    When completa el formulario con nombre, email y contraseña válidos
    Then el sistema crea el Usuario con perfil Estudiante
    And muestra la pantalla de registro exitoso
    And el Estudiante no queda autenticado automáticamente

  Scenario: Registro rechazado por token vencido
    Given una URL de registro con un token cuyo expira_en ya pasó
    When completa el formulario
    Then el sistema muestra la pantalla de error de registro
    And el mensaje no distingue el motivo del rechazo

  Scenario: Registro rechazado por token ya usado
    Given una URL de registro con un token ya usado
    When completa el formulario
    Then el sistema muestra la misma pantalla de error que ante un token vencido

  Scenario: Registro rechazado por token inexistente
    Given una URL de registro con un token que no corresponde a ninguna invitación
    When completa el formulario
    Then el sistema muestra la misma pantalla de error que ante un token vencido

  Scenario: Registro rechazado por email ya registrado
    Given una URL de registro con un token vigente
    When completa el formulario con un email ya registrado
    Then el sistema muestra el error en el propio formulario
    And no navega a la pantalla de error de token
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — consume un endpoint ya implementado (`ADR-012`), sin decisiones nuevas.

**Capa(s) afectadas:**
- [x] Frontend — `frontend/src/pages/Registro.tsx`, `RegistroError.tsx`, `RegistroExito.tsx`
- [ ] Backend — sin cambios

---

## Fuente de verdad UX

`docs/design/ux/wireframes-identidad.md` §2.3 (`#registro`), §2.4 (`#registro-error`), §2.5
(`#registro-exito`), §3 (responsive). Prototipo navegable: `docs/design/ux/prototipos/`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/pages/Registro.tsx` | Formulario de registro — lee `token` de query param |
| `frontend/src/pages/RegistroError.tsx` | Pantalla de error genérico de token inválido/vencido/usado |
| `frontend/src/pages/RegistroExito.tsx` | Confirmación de registro exitoso |
| `frontend/src/router.tsx` | Reemplazar el placeholder de `/registro` por las pantallas reales |

---

## Referencias

- Relacionada con: `US-1.1.2`, `US-1.1.3` (backend), `US-1.1.6` (infraestructura, precondición)
- Candidatas: `docs/plans/inc1/inc1-candidatas.md` §Iteración 2
- Issue: #25

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
