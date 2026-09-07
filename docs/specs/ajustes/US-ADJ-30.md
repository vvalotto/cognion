# US-ADJ-30: Home del Administrador

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 4-ADJ — Portal de Entrada y Validación E2E`, Iteración 1b
**Tipo**: `feature` (pantalla nueva, frontend puro)
**Bounded Context**: ninguno específico — pantalla de entrada, sin lógica de negocio
**Origen**: `docs/plans/inc4-adj/inc4-adj-candidatas.md` §Iteración 1b. Depende de `US-ADJ-27`
(ya cerrada). Última US de la Iteración 1b — la cierra completa junto con `US-ADJ-28`/`29`.

---

## Fuente de verdad UX

`docs/design/ux/wireframes-portal-entrada.md` §2.3. Prototipo navegable:
`docs/design/ux/prototipos/portal-entrada.html` (`#home-admin`).

---

## Descripcion (lenguaje de negocio)

Como **Administrador**,
quiero **una pantalla de inicio con accesos directos a mis áreas**
para que **no salte directo a "Alta de Docente" en cada login**.

---

## Contexto del dominio

### Problema

A diferencia de Docente/Estudiante (que ya caían en `InicioPlaceholder`), el Administrador
nunca pasó por `/` — `RUTA_POST_LOGIN[administrador]` en `Login.tsx` lo manda directo a
`/docentes/nuevo` desde que existe el login (`US-1.1.9`). Sin gap de backend nuevo: mismo
saludo genérico ya decidido en `US-ADJ-28`/`29` ("Hola, Administrador").

### Alcance del fix

**Frontend puro** — las 3 rutas destino ya existen y ya están protegidas por `RequireRole`.

1. Pantalla nueva `HomeAdministrador.tsx`, mismo patrón que `HomeDocente.tsx`/
   `HomeEstudiante.tsx`.
2. 3 cards de acceso directo:
   - **Comisiones** → `/comisiones`
   - **Alta de Docente** → `/docentes/nuevo`
   - **Cuentas** → `/cuentas`
3. `Inicio.tsx` gana la rama `rol === "administrador"` → `<HomeAdministrador />` (con esto,
   `Inicio.tsx` ya no necesita el fallback a `InicioPlaceholder` para ningún rol autenticado
   — el placeholder queda solo como fallback defensivo si `rol` es `undefined`).
4. `Login.tsx`: `RUTA_POST_LOGIN.administrador` pasa de `"/docentes/nuevo"` a `"/"` — mismo
   valor que Docente/Estudiante.

**Fuera de alcance de esta US:**
- Contenido dinámico (contadores, notificaciones) — solo navegación.

---

## Especificacion del comportamiento

### Precondicion

- Login exitoso de Administrador navega directo a `/docentes/nuevo`.
- `/` (si se navega manualmente) renderiza `InicioPlaceholder` para Administrador.

### Postcondicion

- Login exitoso de Administrador navega a `/`, que muestra el saludo y 3 cards de acceso.
- Un click en cualquier card navega a la ruta correspondiente.
- El ítem "Inicio" del menú (`AppNav`) queda resaltado en esta pantalla.

### Invariantes

Ninguna — frontend puro, sin dominio.

---

## Criterios de aceptacion

```gherkin
Feature: Home del Administrador (US-ADJ-30)

  Scenario: Administrador ve sus 3 cards de acceso
    Given un Administrador autenticado
    When navega a "/"
    Then ve las cards Comisiones, Alta de Docente y Cuentas

  Scenario: Click en una card navega a su ruta
    Given un Administrador autenticado en "/"
    When hace clic en la card "Comisiones"
    Then la pantalla muestra el contenido de /comisiones

  Scenario: Login de Administrador navega a la Home, no a Alta de Docente
    Given un Administrador hace login exitoso
    Then la pantalla siguiente es la Home del Administrador, no /docentes/nuevo directamente
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] Sí
- [x] No — pantalla de presentación pura, mismo patrón que `US-ADJ-28`/`29`.

**Capa(s) afectadas:**
- [x] Frontend — `HomeAdministrador.tsx` (nuevo), `Inicio.tsx` (rama nueva), `Login.tsx`
  (`RUTA_POST_LOGIN`)

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/pages/HomeAdministrador.tsx` (nuevo) | Pantalla de home, 3 cards |
| `frontend/src/pages/Inicio.tsx` | Agrega la rama `rol === "administrador"` |
| `frontend/src/pages/identidad/Login.tsx` | `RUTA_POST_LOGIN.administrador` → `"/"` |

---

## Referencias

- Incremento: 4-ADJ
- `docs/plans/inc4-adj/inc4-adj-candidatas.md` §Iteración 1b
- `docs/design/ux/wireframes-portal-entrada.md` §2.3
- Issue: [#275](https://github.com/vvalotto/cognion/issues/275)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
