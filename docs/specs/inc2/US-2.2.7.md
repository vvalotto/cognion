# US-2.2.7: Administrador ve el detalle de una cuenta y resetea/desbloquea (UI)

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-2.2`
**Tipo**: `feat frontend`
**Agregado principal afectado**: — (consume `US-2.2.3`/`US-2.2.4`, sin lógica de dominio propia en el frontend)
**Bounded Context**: Identidad

---

## Descripcion (lenguaje de negocio)

Como **Administrador**,
quiero **ver el detalle de una cuenta y, si hace falta, resetear su contraseña**
para **resolver un bloqueo o un pedido de recuperación completo, desde la aplicación
(RF-03)**.

---

## Contexto del dominio

### Problema

`GET /usuarios/{id}` (`US-2.2.3`) y `POST /usuarios/{id}/resetear-password` (`US-2.2.4`)
existen en el backend, pero sin esta US no hay forma de usarlos desde la app real. Cubre tres
pantallas del wireframe como un único flujo (mismo criterio que `US-2.1.11`, que agrupó tres
pantallas de carga de pregunta en una sola US).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Endpoint consumido | `GET /usuarios/{id}` | Ya existe (`US-2.2.3`) |
| Endpoint consumido | `POST /usuarios/{id}/resetear-password` | Ya existe (`US-2.2.4`) |

---

## Especificacion del comportamiento

### Precondicion

- `US-2.2.6` implementada (se navega al detalle desde una fila del listado).

### Postcondicion

- El detalle muestra los datos de la cuenta y, si `bloqueada = true`, una alerta explicando
  el motivo (`wireframes-cuentas-administracion.md` §2.2).
- "Resetear contraseña y desbloquear" navega al formulario de reseteo.
- El formulario valida en cliente: nueva contraseña ≥ 8 caracteres, coincidencia entre
  contraseña y confirmación — antes de llamar al backend.
- Confirmar el reseteo → ejecuta `POST /usuarios/{id}/resetear-password` y navega a la
  pantalla de confirmación de éxito.
- Cancelar → vuelve al detalle sin ejecutar ningún cambio.
- Desde la confirmación de éxito, "Volver al listado de cuentas" navega a `US-2.2.6`.

### Invariantes

| ID | Invariante |
|----|------------|
| — | N/A — el frontend valida en cliente por UX, pero la validación de dominio real (INV-ID-11) ya la aplica el backend en `US-2.2.4`. |

---

## Criterios de aceptacion

```gherkin
Feature: Detalle de cuenta y reseteo desde la UI (US-2.2.7)

  Scenario: Ver el detalle de una cuenta bloqueada
    Given un Administrador navega al detalle de una cuenta con bloqueada = true
    Then ve una alerta indicando que la cuenta está bloqueada

  Scenario: Resetear contraseña exitosamente
    Given un Administrador en el formulario de reseteo de una cuenta
    When ingresa una contraseña nueva válida y confirma
    Then el sistema ejecuta el reseteo
    And navega a la pantalla de confirmación
    And la cuenta ya no aparece como bloqueada al volver a consultarla

  Scenario: Cancelar el reseteo
    Given un Administrador en el formulario de reseteo
    When hace clic en "Cancelar"
    Then el sistema vuelve al detalle de la cuenta sin ejecutar ningún cambio
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — consume endpoints ya implementados.

**Capa(s) afectadas:**
- [x] Frontend — `frontend/src/lib/cuentas-api.ts` (extiende el cliente de `US-2.2.6` con
  `obtenerCuenta`/`resetearPassword`), `frontend/src/pages/CuentaDetalle.tsx`,
  `frontend/src/pages/ResetearPassword.tsx`, `frontend/src/pages/CuentaReseteada.tsx`
- [ ] Backend — sin cambios

---

## Fuente de verdad UX

`docs/design/ux/wireframes-cuentas-administracion.md` §2.2-§2.4 (`#cuenta-detalle`,
`#cuenta-resetear`, `#cuenta-reseteada`). Prototipo navegable:
`docs/design/ux/prototipos/identidad-cuentas-administracion.html`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/lib/cuentas-api.ts` | `obtenerCuenta(id)`, `resetearPassword(id, passwordNueva)` |
| `frontend/src/pages/CuentaDetalle.tsx` | Datos de la cuenta + alerta de bloqueo + botón de reseteo |
| `frontend/src/pages/ResetearPassword.tsx` | Formulario con validación de cliente |
| `frontend/src/pages/CuentaReseteada.tsx` | Confirmación de éxito |
| `frontend/src/router.tsx` | Rutas `/cuentas/:id`, `/cuentas/:id/resetear-password`, protegidas con `RequireRole rol="administrador"` |

---

## Referencias

- Relacionada con: `US-2.2.3`, `US-2.2.4` (backend), `US-2.2.6` (navegación de entrada)
- Candidatas: `docs/plans/inc2/inc2-candidatas.md` §Iteración 2 — Frontend

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
