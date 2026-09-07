# US-ADJ-27: Menú de navegación persistente en AppLayout

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 4-ADJ — Portal de Entrada y Validación E2E`, Iteración 1b
**Tipo**: `feature` (componente de navegación nuevo, frontend puro)
**Bounded Context**: ninguno específico — transversal a los 4 BC del frontend
**Origen**: `docs/plans/inc4-adj/inc4-adj-candidatas.md` §Iteración 1b. Primera US de la
Iteración 1b — las 3 homes (`US-ADJ-28`/`29`/`30`) dependen de este componente si el
wireframe integra menú + contenido en una sola pantalla, pero el menú en sí no depende de
ninguna de ellas.

---

## Fuente de verdad UX

`docs/design/ux/wireframes-portal-entrada.md` §2.4 (`.app-nav`) y §1 (identidad visual).
Prototipo navegable: `docs/design/ux/prototipos/portal-entrada.html` (clase `.app-nav`,
todas las pantallas de home).

---

## Descripcion (lenguaje de negocio)

Como **usuario autenticado** (Docente, Estudiante o Administrador),
quiero **ver un menú de navegación persistente en toda pantalla post-login**
para que **pueda moverme entre las áreas de mi rol sin escribir URLs de memoria**.

---

## Contexto del dominio

### Problema

`AppLayout.tsx` hoy solo tiene un header con logo y badge de rol (`session.rol`), sin ningún
enlace de navegación — el usuario que aterriza en cualquier pantalla no tiene forma de
moverse a otra área sin escribir la URL a mano. Confirmado en `HITO-9` (ninguna de las 4
rondas de UAT manual recorrió el camino real login → función) y agravado porque, dentro de un
mismo rol, tampoco hay navegación cruzada entre áreas top-level (ej. el Docente en `/materias`
no tiene forma de llegar a `/actividad-evaluativa/materias` sin la URL).

### Alcance del fix

**Frontend puro** — todas las rutas destino ya existen y ya están protegidas por
`RequireRole` (`US-1.1.9`). Sin backend nuevo.

1. Componente nuevo `AppNav.tsx`, integrado en `AppLayout.tsx` debajo del header actual.
2. Ítems condicionados por `session.rol` (wireframe §2.1–§2.3):
   - **Docente:** Inicio (`/`) · Banco de Preguntas (`/materias`) · Actividades
     (`/actividad-evaluativa/materias`) · Desempeño por alumno
     (`/analytics/desempeno-por-alumno`) · Desempeño por tema (`/analytics/desempeno-por-tema`)
   - **Estudiante:** Inicio (`/`) · Mis Actividades (`/mis-actividades/materias`) · Mi
     Desempeño (`/analytics/mi-desempeno`)
   - **Administrador:** Inicio (`/`) · Comisiones (`/comisiones`) · Docentes
     (`/docentes/nuevo`) · Cuentas (`/cuentas`)
3. Ítem de la sección actual resaltado (subrayado + color primario, `.app-nav a.current` en
   el prototipo) — un ítem está "activo" si `location.pathname` coincide exactamente con su
   ruta (`/`) o empieza con ella seguida de `/` (para que sub-rutas como
   `/materias/:id/banco` sigan resaltando "Banco de Preguntas").
4. Sin sesión activa (`AuthLayout`, `/login`/`/registro`), el menú no se muestra — mismo
   criterio que el badge de rol actual en `AppLayout.tsx`.

**Fuera de alcance de esta US:**
- Contenido de las 3 homes (`InicioPlaceholder` sigue en `/`) — se reemplaza en
  `US-ADJ-28`/`29`/`30`.
- Badges de notificación, buscador global — sin read model para eso hoy (wireframe §2.4,
  "Fuera de alcance").
- Submenús o agrupamiento — ítems sueltos (decisión ya tomada en
  `docs/design/domain/portal-entrada-modelo.md` §3).

---

## Especificacion del comportamiento

### Precondicion

- `AppLayout.tsx` no tiene ningún enlace de navegación, solo logo + badge de rol.
- El usuario en `/materias` (Docente) no tiene forma de llegar a
  `/actividad-evaluativa/materias` sin escribir la URL.

### Postcondicion

- Un usuario autenticado con rol Docente ve, en cualquier pantalla, los 5 ítems de su menú;
  Estudiante ve 3; Administrador ve 4.
- El ítem correspondiente a la sección donde está parado aparece resaltado.
- Un click en cualquier ítem navega a la ruta correspondiente sin recarga completa de página.
- Un usuario sin sesión activa (pantallas de `AuthLayout`) no ve el menú.

### Invariantes

Ninguna — sin dominio ni backend involucrado.

---

## Criterios de aceptacion

```gherkin
Feature: Menú de navegación persistente en AppLayout (US-ADJ-27)

  Scenario: Docente ve sus 5 ítems de menú
    Given un Docente autenticado
    When ve cualquier pantalla post-login
    Then el menú muestra Inicio, Banco de Preguntas, Actividades, Desempeño por alumno y
      Desempeño por tema

  Scenario: Estudiante ve sus 3 ítems de menú
    Given un Estudiante autenticado
    When ve cualquier pantalla post-login
    Then el menú muestra Inicio, Mis Actividades y Mi Desempeño

  Scenario: Administrador ve sus 4 ítems de menú
    Given un Administrador autenticado
    When ve cualquier pantalla post-login
    Then el menú muestra Inicio, Comisiones, Docentes y Cuentas

  Scenario: El ítem de la sección actual queda resaltado
    Given un Docente autenticado en /actividad-evaluativa/materias
    When ve el menú
    Then el ítem "Actividades" aparece marcado como actual

  Scenario: Click en un ítem navega a su ruta
    Given un Docente autenticado en Inicio
    When hace clic en "Banco de Preguntas"
    Then la pantalla muestra el contenido de /materias

  Scenario: Sin sesión activa no se muestra el menú
    Given un usuario sin sesión activa
    When ve una pantalla de AppLayout
    Then no aparece ningún ítem de navegación
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] Sí
- [x] No — componente de presentación puro, sin lógica de negocio ni backend nuevo.

**Capa(s) afectadas:**
- [x] Frontend — `AppNav.tsx` (nuevo), `AppLayout.tsx` (integra el componente)

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/components/AppNav.tsx` (nuevo) | Menú de navegación condicionado por `session.rol`, ítem actual resaltado |
| `frontend/src/layouts/AppLayout.tsx` | Integra `<AppNav />` debajo del header, solo si hay sesión |

---

## Referencias

- Incremento: 4-ADJ
- `docs/plans/inc4-adj/inc4-adj-candidatas.md` §Iteración 1b
- `docs/design/ux/wireframes-portal-entrada.md` §2.4
- `docs/design/domain/portal-entrada-modelo.md` §2, §3
- Issue: [#272](https://github.com/vvalotto/cognion/issues/272)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
