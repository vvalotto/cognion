# US-ADJ-37: Descubribilidad — Cambiar contraseña y Cerrar sesión en el menú

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 5-ADJ — Identidad Autoservicio y Analytics del Docente`,
Iteración 1
**Tipo**: `feature` (menú desplegable nuevo sobre el header existente, frontend puro)
**Bounded Context**: ninguno específico — componente transversal de UI (`AppLayout.tsx`)
**Origen**: `docs/plans/inc5-adj/inc5-adj-candidatas.md` §Iteración 1. Hallazgos 3 y 6 de
`hallazgos-cognion.md` ("Cambiar contraseña" sin descubribilidad, "Logout o cierre de
sesión"). Independiente de `US-ADJ-35`/`36` — sin orden obligatorio.

---

## Fuente de verdad UX

`docs/design/ux/wireframes-identidad-autoservicio.md` §6 ("Menú de usuario"). Prototipo
navegable: `docs/design/ux/prototipos/identidad-autoservicio.html` (`#menu-usuario`).

---

## Descripcion (lenguaje de negocio)

Como **cualquier usuario autenticado** (Docente, Estudiante o Administrador),
quiero **encontrar "Cambiar contraseña" y "Cerrar sesión" en un lugar visible**
para **usar funciones que ya existen en el sistema pero hoy no tienen ningún punto de entrada
por clic**.

---

## Contexto del dominio

### Problema

Dos funciones ya implementadas y funcionales quedaron sin punto de entrada visible, mismo
patrón de gap ya documentado en el proyecto ("portal de entrada sin dueño de producto",
`HITO-9`):

1. **Cambiar contraseña** (`US-2.2.8`): pantalla `CambiarPassword.tsx` completa, ruta
   `/mi-cuenta/cambiar-password` registrada en `router.tsx` sin `RequireRole` (accesible a
   cualquier autenticado) — pero ningún `<Link>` ni `navigate()` apunta a ella desde
   `AppNav.tsx` ni desde ninguna de las 3 `Home*.tsx`. Solo alcanzable tecleando la URL de
   memoria.
2. **Cerrar sesión**: `clearSession()` existe (`frontend/src/lib/session.ts:24`, borra
   `localStorage.removeItem("cognion.session")`) pero se invoca **solo** desde el interceptor
   de error 401 de `api-client.ts` — logout automático al expirar el JWT, sin ningún botón que
   lo dispare voluntariamente.

El bloque de avatar/nombre del header (`AppLayout.tsx:35-45`) hoy es puramente informativo
(`<div>` estático con iniciales + nombre + rol) — es el punto de entrada natural para ambas
acciones, ya visible en toda pantalla post-login.

### Alcance del fix

**Frontend puro** — ambas funciones destino ya existen y funcionan, sin cambios de backend.

1. `AppLayout.tsx`: el `<div>` estático de avatar/nombre (líneas 35-45) se reemplaza por un
   trigger de menú desplegable, usando `@base-ui/react/menu` (dependencia ya instalada,
   `package.json:15` — `@base-ui/react@^1.6.0` — sin agregar ninguna librería nueva).
2. Contenido del menú: encabezado con nombre + rol (mismo dato ya mostrado hoy), separador, dos
   ítems — "🔑 Cambiar contraseña" (`<Link to="/mi-cuenta/cambiar-password">`) y
   "↩ Cerrar sesión" (`onClick` que llama `clearSession()` y `navigate("/login")`).
3. Mismo menú para los 3 roles — sin lógica condicional por `session.rol` en el contenido.

**Fuera de alcance de esta US:**
- Cualquier cambio a `CambiarPassword.tsx` o al comportamiento de `clearSession()` — ambos ya
  funcionan, esta US solo agrega el punto de entrada.
- Confirmación ("¿Seguro que querés cerrar sesión?") antes de cerrar sesión — no pedido en el
  wireframe, acción de bajo riesgo (no destruye datos).

---

## Especificacion del comportamiento

### Precondicion

- El bloque de avatar/nombre de `AppLayout.tsx` es estático, sin interacción.
- `/mi-cuenta/cambiar-password` no tiene ningún link entrante desde la navegación.
- `clearSession()` solo se invoca desde el interceptor 401.

### Postcondicion

- Un usuario autenticado hace clic en su avatar/nombre en cualquier pantalla post-login y ve
  un menú con "Cambiar contraseña" y "Cerrar sesión".
- "Cambiar contraseña" navega a la pantalla ya existente.
- "Cerrar sesión" limpia la sesión local y redirige a `/login`.

### Invariantes

N/A — frontend puro, sin dominio.

---

## Criterios de aceptacion

```gherkin
Feature: Descubribilidad — Cambiar contraseña y Cerrar sesión (US-ADJ-37)

  Scenario: Abrir el menú de usuario
    Given un usuario autenticado en cualquier pantalla post-login
    When hace clic en su avatar/nombre del header
    Then se abre un menú con "Cambiar contraseña" y "Cerrar sesión"

  Scenario: Navegar a Cambiar contraseña desde el menú
    Given el menú de usuario está abierto
    When hace clic en "Cambiar contraseña"
    Then la pantalla actual es /mi-cuenta/cambiar-password

  Scenario: Cerrar sesión desde el menú
    Given el menú de usuario está abierto
    When hace clic en "Cerrar sesión"
    Then la sesión local se limpia
    And la pantalla actual es /login

  Scenario: Mismo menú para los 3 roles
    Given usuarios autenticados con rol Docente, Estudiante y Administrador, por separado
    When cada uno abre su menú de usuario
    Then los tres ven exactamente los mismos dos ítems
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] Sí
- [x] No — usa un primitivo ya disponible en `node_modules` (`@base-ui/react/menu`), mismo
  patrón que `select.tsx` envolviendo un primitivo nativo/de librería con las clases del
  proyecto.

**Capa(s) afectadas:**
- [x] Frontend — `layouts/AppLayout.tsx` (bloque de avatar/nombre reemplazado por menú)

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/layouts/AppLayout.tsx` | Bloque de avatar/nombre pasa a trigger de `@base-ui/react/menu` con 2 ítems |

---

## Referencias

- Incremento: 5-ADJ
- `docs/plans/inc5-adj/inc5-adj-candidatas.md` §Iteración 1
- `docs/design/ux/wireframes-identidad-autoservicio.md` §6
- Issue: [#331](https://github.com/vvalotto/cognion/issues/331)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
