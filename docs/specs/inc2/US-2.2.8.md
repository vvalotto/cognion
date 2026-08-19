# US-2.2.8: Cualquier usuario autenticado cambia su propia contraseña (UI)

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-2.2`
**Tipo**: `feat frontend`
**Agregado principal afectado**: — (consume `US-2.2.5`, sin lógica de dominio propia en el frontend)
**Bounded Context**: Identidad

---

## Descripcion (lenguaje de negocio)

Como **Usuario autenticado** (Administrador, Docente o Estudiante),
quiero **cambiar mi propia contraseña desde la aplicación**
para **actualizarla cuando quiera, sin pedirle ayuda al Administrador (RF-19)**.

---

## Contexto del dominio

### Problema

`PUT /usuarios/me/password` (`US-2.2.5`) existe en el backend, pero sin esta US no hay
pantalla que lo use. A diferencia del resto de la Iteración 2, esta pantalla es accesible
para los tres roles, no solo Administrador — se ubica fuera del área de administración
(sección "Mi cuenta").

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Endpoint consumido | `PUT /usuarios/me/password` | Ya existe (`US-2.2.5`) |

---

## Especificacion del comportamiento

### Precondicion

- Cualquier usuario autenticado (JWT válido, sin restricción de rol).

### Postcondicion

- El formulario valida en cliente: contraseña nueva ≥ 8 caracteres, coincidencia entre nueva
  y confirmación — antes de llamar al backend.
- Envío exitoso → navega a la confirmación de éxito; el mensaje aclara que la sesión sigue
  activa.
- Rechazo por `PasswordActualIncorrecta` → la pantalla muestra la alerta de error con la
  cantidad de intentos restantes antes del bloqueo automático (`intentos_fallidos_password`,
  expuesto por el backend en la respuesta de error), y limpia los campos para reintentar.
- Rechazo por cuenta bloqueada (`CuentaBloqueadaError`, tercer fallo alcanzado) → mensaje
  explícito de que la cuenta quedó bloqueada y debe contactar a un Administrador — no un
  simple "intentos restantes: 0".

### Invariantes

| ID | Invariante |
|----|------------|
| — | N/A — la validación de dominio real (INV-ID-10, INV-ID-11) ya la aplica el backend en `US-2.2.5`. |

---

## Criterios de aceptacion

```gherkin
Feature: Cambio de contraseña propio desde la UI (US-2.2.8)

  Scenario: Cambio exitoso
    Given un Usuario autenticado en la pantalla "Cambiar mi contraseña"
    When ingresa su contraseña actual correcta y una nueva válida
    Then el sistema ejecuta el cambio
    And navega a la confirmación de éxito
    And no requiere volver a iniciar sesión

  Scenario: Contraseña actual incorrecta
    Given un Usuario autenticado en la pantalla "Cambiar mi contraseña"
    When ingresa una contraseña actual incorrecta
    Then el sistema muestra la alerta de error con los intentos restantes
    And los campos quedan vacíos para reintentar

  Scenario: La cuenta queda bloqueada tras el tercer fallo
    Given un Usuario con 2 intentos fallidos previos de este flujo
    When ingresa la contraseña actual incorrecta una vez más
    Then el sistema muestra que la cuenta quedó bloqueada
    And indica que debe contactar a un Administrador
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — consume un endpoint ya implementado.

**Capa(s) afectadas:**
- [x] Frontend — `frontend/src/lib/cuentas-api.ts` (extiende con `cambiarPassword`),
  `frontend/src/pages/CambiarPassword.tsx`
- [ ] Backend — sin cambios

---

## Fuente de verdad UX

`docs/design/ux/wireframes-cuentas-administracion.md` §2.5-§2.7 (`#cambiar-password`,
`#cambiar-password-error`, `#cambiar-password-exito`). Prototipo navegable:
`docs/design/ux/prototipos/identidad-cuentas-administracion.html`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/lib/cuentas-api.ts` | `cambiarPassword(passwordActual, passwordNueva)` |
| `frontend/src/pages/CambiarPassword.tsx` | Formulario, manejo de error/éxito en la misma pantalla (sin ruta separada para el estado de error, a diferencia del prototipo que lo modela como pantalla aparte por claridad de wireframe) |
| `frontend/src/router.tsx` | Ruta `/mi-cuenta/cambiar-password`, accesible para cualquier rol autenticado (sin `RequireRole`) |

---

## Referencias

- Relacionada con: `US-2.2.5` (backend), `US-2.2.9` (mismo mecanismo de bloqueo, distinto flujo)
- Candidatas: `docs/plans/inc2/inc2-candidatas.md` §Iteración 2 — Frontend

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
